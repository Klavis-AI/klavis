import contextlib
import logging
import os
import json
from collections.abc import AsyncIterator
from typing import Any, Dict
import anyio

import click
from dotenv import load_dotenv
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from contextvars import ContextVar

from tools import (
    clear_completed_tasks as gt_clear_completed_tasks,
    create_task as gt_create_task,
    create_tasklist as gt_create_tasklist,
    delete_task as gt_delete_task,
    delete_tasklist as gt_delete_tasklist,
    get_task as gt_get_task,
    get_tasklist as gt_get_tasklist,
    list_tasks as gt_list_tasks,
    list_tasklists as gt_list_tasklists,
    move_task as gt_move_task,
    patch_task as gt_patch_task,
    patch_tasklist as gt_patch_tasklist,
    update_task as gt_update_task,
    update_tasklist as gt_update_tasklist,
)

auth_token_context = ContextVar("auth_token", default=None)

logger = logging.getLogger(__name__)

load_dotenv()

GOOGLE_TASKS_MCP_SERVER_PORT = int(os.getenv("GOOGLE_TASKS_MCP_SERVER_PORT", "5000"))




@click.command()
@click.option("--port", default=GOOGLE_TASKS_MCP_SERVER_PORT, help="Port to listen on for HTTP")
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@click.option(
    "--json-response",
    is_flag=True,
    default=False,
    help="Enable JSON responses for StreamableHTTP instead of SSE streams",
)
def main(
    port: int,
    log_level: str,
    json_response: bool,
) -> int:
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Suppress noisy ClosedResourceError logs from StreamableHTTP when clients
    # close their write stream (normal shutdown behavior)
    class _SuppressClosedResourceError(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401
            if record.name != "mcp.server.streamable_http":
                return True
            message_text = record.getMessage()
            try:
                exc_type = record.exc_info[0] if record.exc_info else None
                is_closed = (
                    exc_type is not None and getattr(exc_type, "__name__", "") == "ClosedResourceError"
                )
            except Exception:
                is_closed = False

            # Drop the specific router error that occurs on normal client close
            if is_closed and "Error in message router" in message_text:
                return False

            # Demote any residual mentions to INFO to avoid alarming logs
            if "ClosedResourceError" in message_text:
                record.levelno = logging.INFO
                record.levelname = "INFO"
            return True

    logging.getLogger("mcp.server.streamable_http").addFilter(_SuppressClosedResourceError())


    app = Server("google-tasks-mcp-server")

    # ---------------------- list_tools ----------------------
    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            # Tasklists
            types.Tool(
                name="google_list_tasklists",
                description="List all Google Tasks tasklists for the authenticated user.",
                inputSchema={"type": "object", "properties": {}},
            ),
            types.Tool(
                name="google_get_tasklist",
                description="Get a specific tasklist by its ID.",
                inputSchema={
                    "type": "object",
                    "required": ["tasklist_id"],
                    "properties": {
                        "tasklist_id": {
                            "type": "string",
                            "description": "ID of the tasklist to retrieve.",
                        }
                    },
                },
            ),
            types.Tool(
                name="google_create_tasklist",
                description="Create a new tasklist.",
                inputSchema={
                    "type": "object",
                    "required": ["title"],
                    "properties": {
                        "title": {"type": "string", "description": "Title of the tasklist."}
                    },
                },
            ),
            types.Tool(
                name="google_delete_tasklist",
                description="Delete a tasklist by ID (along with all tasks within).",
                inputSchema={
                    "type": "object",
                    "required": ["tasklist_id"],
                    "properties": {
                        "tasklist_id": {
                            "type": "string",
                            "description": "ID of the tasklist to delete.",
                        }
                    },
                },
            ),
            types.Tool(
                name="google_patch_tasklist",
                description="Patch fields on a tasklist (e.g., title).",
                inputSchema={
                    "type": "object",
                    "required": ["tasklist_id"],
                    "properties": {
                        "tasklist_id": {"type": "string"},
                        "title": {"type": "string"},
                    },
                },
            ),
            types.Tool(
                name="google_update_tasklist",
                description="Update a tasklist (full update semantics).",
                inputSchema={
                    "type": "object",
                    "required": ["tasklist_id"],
                    "properties": {
                        "tasklist_id": {"type": "string"},
                        "title": {"type": "string"},
                    },
                },
            ),
            # Tasks
            types.Tool(
                name="google_list_tasks",
                description="List tasks in a tasklist (optionally hide completed).",
                inputSchema={
                    "type": "object",
                    "required": ["tasklist_id"],
                    "properties": {
                        "tasklist_id": {"type": "string", "description": "Tasklist ID."},
                        "show_completed": {
                            "type": "boolean",
                            "description": "Whether to include completed tasks (default true).",
                            "default": True,
                        },
                    },
                },
            ),
            types.Tool(
                name="google_get_task",
                description="Get a single task by ID.",
                inputSchema={
                    "type": "object",
                    "required": ["tasklist_id", "task_id"],
                    "properties": {
                        "tasklist_id": {"type": "string", "description": "Tasklist ID."},
                        "task_id": {"type": "string", "description": "Task ID."},
                    },
                },
            ),
            types.Tool(
                name="google_create_task",
                description="Create a new task in the specified tasklist.",
                inputSchema={
                    "type": "object",
                    "required": ["tasklist_id", "title"],
                    "properties": {
                        "tasklist_id": {"type": "string", "description": "Tasklist ID."},
                        "title": {"type": "string", "description": "Task title."},
                        "notes": {"type": "string", "description": "Optional notes."},
                        "due": {"type": "string", "description": "Due date ISO 8601."},
                        "parent": {"type": "string", "description": "Parent task ID if creating a subtask."},
                        "position": {
                            "type": "string",
                            "description": "Insert position relative to other tasks (optional).",
                        },
                    },
                },
            ),
            types.Tool(
                name="google_update_task",
                description="Update an existing task (provide only fields to change).",
                inputSchema={
                    "type": "object",
                    "required": ["tasklist_id", "task_id"],
                    "properties": {
                        "tasklist_id": {"type": "string", "description": "Tasklist ID."},
                        "task_id": {"type": "string", "description": "Task ID."},
                        "title": {"type": "string", "description": "New title."},
                        "notes": {"type": "string", "description": "New notes."},
                        "due": {"type": "string", "description": "New due date ISO 8601."},
                        "status": {
                            "type": "string",
                            "description": "Task status (needsAction or completed).",
                        },
                        "parent": {"type": "string", "description": "New parent task ID."},
                        "position": {"type": "string", "description": "New task position."},
                    },
                },
            ),
            types.Tool(
                name="google_move_task",
                description="Move a task under a different parent or position.",
                inputSchema={
                    "type": "object",
                    "required": ["tasklist_id", "task_id"],
                    "properties": {
                        "tasklist_id": {"type": "string", "description": "Tasklist ID."},
                        "task_id": {"type": "string", "description": "Task ID."},
                        "parent": {"type": "string", "description": "New parent task ID (optional)."},
                        "previous": {"type": "string", "description": "Move after this task ID (optional)."},
                    },
                },
            ),
            types.Tool(
                name="google_clear_completed_tasks",
                description="Delete all completed tasks from a tasklist.",
                inputSchema={
                    "type": "object",
                    "required": ["tasklist_id"],
                    "properties": {
                        "tasklist_id": {"type": "string", "description": "Tasklist ID."}
                    },
                },
            ),
            types.Tool(
                name="google_delete_task",
                description="Delete a task by ID.",
                inputSchema={
                    "type": "object",
                    "required": ["tasklist_id", "task_id"],
                    "properties": {
                        "tasklist_id": {"type": "string", "description": "Tasklist ID."},
                        "task_id": {"type": "string", "description": "Task ID."},
                    },
                },
            ),
            types.Tool(
                name="google_patch_task",
                description="Patch fields on a task (partial update).",
                inputSchema={
                    "type": "object",
                    "required": ["tasklist_id", "task_id"],
                    "properties": {
                        "tasklist_id": {"type": "string"},
                        "task_id": {"type": "string"},
                        "title": {"type": "string"},
                        "notes": {"type": "string"},
                        "due": {"type": "string"},
                        "status": {"type": "string"},
                        "parent": {"type": "string"},
                        "position": {"type": "string"},
                    },
                },
            ),
        ]

    # ---------------------- call_tool ----------------------
    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        # Log the tool call with name and arguments
        logger.info(f"Tool called: {name}")
        logger.debug(f"Tool arguments: {json.dumps(arguments, indent=2)}")

        if name == "google_list_tasklists":
            try:
                result = gt_list_tasklists()
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        elif name == "google_get_tasklist":
            try:
                result = gt_get_tasklist(arguments["tasklist_id"])
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        elif name == "google_create_tasklist":
            try:
                result = gt_create_tasklist(arguments["title"])
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        elif name == "google_delete_tasklist":
            try:
                gt_delete_tasklist(arguments["tasklist_id"])
                result = {"status": "deleted"}
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        elif name == "google_patch_tasklist":
            try:
                fields = arguments.copy()
                tasklist_id = fields.pop("tasklist_id")
                result = gt_patch_tasklist(tasklist_id, **fields)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        elif name == "google_update_tasklist":
            try:
                result = gt_update_tasklist(
                    arguments["tasklist_id"], arguments.get("title")
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        elif name == "google_list_tasks":
            try:
                result = gt_list_tasks(
                    arguments["tasklist_id"], arguments.get("show_completed", True)
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        elif name == "google_get_task":
            try:
                result = gt_get_task(
                    arguments["tasklist_id"], arguments["task_id"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        elif name == "google_create_task":
            try:
                result = gt_create_task(
                    arguments["tasklist_id"],
                    arguments["title"],
                    arguments.get("notes"),
                    arguments.get("due"),
                    arguments.get("parent"),
                    arguments.get("position"),
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        elif name == "google_update_task":
            try:
                updates = arguments.copy()
                tasklist_id = updates.pop("tasklist_id")
                task_id = updates.pop("task_id")
                result = gt_update_task(tasklist_id, task_id, **updates)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        elif name == "google_move_task":
            try:
                result = gt_move_task(
                    arguments["tasklist_id"],
                    arguments["task_id"],
                    arguments.get("parent"),
                    arguments.get("previous"),
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        elif name == "google_clear_completed_tasks":
            try:
                gt_clear_completed_tasks(arguments["tasklist_id"])
                result = {"status": "cleared"}
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        elif name == "google_delete_task":
            try:
                gt_delete_task(arguments["tasklist_id"], arguments["task_id"])
                result = {"status": "deleted"}
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        elif name == "google_patch_task":
            try:
                fields = arguments.copy()
                tasklist_id = fields.pop("tasklist_id")
                task_id = fields.pop("task_id")
                result = gt_patch_task(tasklist_id, task_id, **fields)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        else:
            return [
                types.TextContent(type="text", text=f"Unknown tool: {name}"),
            ]

    # ---------------------- Transports ----------------------

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        """Handle SSE-based MCP connections."""
        logger.info("Handling SSE connection")
        
        # Extract auth token from headers (allow None - will be handled at tool level)
        auth_token = request.headers.get('x-auth-token')
        
        # Set the auth token in context for this request (can be None)
        token = auth_token_context.set(auth_token or "")
        try:
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
        finally:
            auth_token_context.reset(token)
        
        return Response()

    # Set up StreamableHTTP transport
    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,  # Stateless mode - can be changed to use an event store
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        """Handle StreamableHTTP-based MCP connections."""
        logger.info("Handling StreamableHTTP request")
        
        # Extract auth token from headers (allow None - will be handled at tool level)
        headers = dict(scope.get("headers", []))
        auth_token = headers.get(b'x-auth-token')
        if auth_token:
            auth_token = auth_token.decode('utf-8')
        
        # Set the auth token in context for this request (can be None/empty)
        token = auth_token_context.set(auth_token or "")
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            auth_token_context.reset(token)

    @contextlib.asynccontextmanager
    async def lifespan(_: Starlette) -> AsyncIterator[None]:
        """Context manager for session manager."""
        async with session_manager.run():
            logger.info("Application started with dual transports!")
            try:
                yield
            finally:
                logger.info("Application shutting down...")

    # Create an ASGI application with routes for both transports
    starlette_app = Starlette(
        lifespan=lifespan,
        routes=[
            # SSE routes
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),

            # StreamableHTTP route mounted at /mcp; Starlette's Mount handles both /mcp and /mcp/
            Mount("/mcp", app=handle_streamable_http),
        ],
    )

    import uvicorn

    logger.info(f"Starting Google Tasks MCP Server on port {port}")
    # Force lifespan handling ON to ensure session_manager.run() is entered
    uvicorn.run(starlette_app, host="0.0.0.0", port=port, lifespan="on")

    return 0


if __name__ == "__main__":
    exit(main())

