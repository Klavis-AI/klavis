import contextlib
import logging
import os
import json
from collections.abc import AsyncIterator
from typing import Any, Dict

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

from .tools.tasklists import (
    list_tasklists as gt_list_tasklists,
    get_tasklist as gt_get_tasklist,
    create_tasklist as gt_create_tasklist,
    delete_tasklist as gt_delete_tasklist,
)
from .tools.tasks import (
    list_tasks as gt_list_tasks,
    get_task as gt_get_task,
    create_task as gt_create_task,
    update_task as gt_update_task,
    move_task as gt_move_task,
    clear_completed_tasks as gt_clear_completed_tasks,
    delete_task as gt_delete_task,
)

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
        ]

    # ---------------------- call_tool ----------------------
    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[
        types.TextContent | types.ImageContent | types.EmbeddedResource
    ]:
        try:
            if name == "google_list_tasklists":
                result = gt_list_tasklists()
            elif name == "google_get_tasklist":
                result = gt_get_tasklist(arguments["tasklist_id"])
            elif name == "google_create_tasklist":
                result = gt_create_tasklist(arguments["title"])
            elif name == "google_delete_tasklist":
                gt_delete_tasklist(arguments["tasklist_id"])
                result = {"status": "deleted"}
            elif name == "google_list_tasks":
                result = gt_list_tasks(
                    arguments["tasklist_id"],
                    arguments.get("show_completed", True),
                )
            elif name == "google_get_task":
                result = gt_get_task(arguments["tasklist_id"], arguments["task_id"])
            elif name == "google_create_task":
                result = gt_create_task(
                    tasklist_id=arguments["tasklist_id"],
                    title=arguments["title"],
                    notes=arguments.get("notes"),
                    due=arguments.get("due"),
                    parent=arguments.get("parent"),
                    position=arguments.get("position"),
                )
            elif name == "google_update_task":
                updates = arguments.copy()
                tasklist_id = updates.pop("tasklist_id")
                task_id = updates.pop("task_id")
                result = gt_update_task(tasklist_id, task_id, **updates)
            elif name == "google_move_task":
                result = gt_move_task(
                    arguments["tasklist_id"],
                    arguments["task_id"],
                    parent=arguments.get("parent"),
                    previous=arguments.get("previous"),
                )
            elif name == "google_clear_completed_tasks":
                gt_clear_completed_tasks(arguments["tasklist_id"])
                result = {"status": "cleared"}
            elif name == "google_delete_task":
                gt_delete_task(arguments["tasklist_id"], arguments["task_id"])
                result = {"status": "deleted"}
            else:
                return [
                    types.TextContent(type="text", text=f"Unknown tool: {name}"),
                ]

            # Success path
            return [
                types.TextContent(type="text", text=json.dumps(result, indent=2)),
            ]
        except Exception as exc:
            logger.exception("Error executing tool %s: %s", name, exc)
            return [
                types.TextContent(type="text", text=f"Error: {str(exc)}"),
            ]

    # ---------------------- Transports ----------------------

    sse_transport = SseServerTransport("/messages")
    session_manager = StreamableHTTPSessionManager(app=app, event_store=None, json_response=json_response, stateless=True)

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        async with sse_transport.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await app.run(streams[0], streams[1], app.create_initialization_options())
        return Response()

    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(_: Starlette) -> AsyncIterator[None]:
        yield

    starlette_app = Starlette(
        lifespan=lifespan,
        routes=[
            Route("/sse", handle_sse, methods=["GET"]),
            Mount("/mcp", app=handle_streamable_http),
        ],
    )

    import uvicorn

    logger.info(f"Starting Google Tasks MCP Server on port {port}")
    uvicorn.run(starlette_app, host="0.0.0.0", port=port)

    return 0


if __name__ == "__main__":
    exit(main())

