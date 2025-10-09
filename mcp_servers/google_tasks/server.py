import contextlib
import logging
import os
import json
from collections.abc import AsyncIterator
from typing import Any
import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from dotenv import load_dotenv
from googleapiclient.errors import HttpError

try:
    from .tools.utils import (
        ValidationError,
        validate_task_data,
        parse_rfc3339,
        success,
        failure,
        shape_task,
        shape_task_list,
        http_error_to_message,
    )
except ImportError:
    from tools.utils import (
        ValidationError,
        validate_task_data,
        parse_rfc3339,
        success,
        failure,
        shape_task,
        shape_task_list,
        http_error_to_message,
    )

logger = logging.getLogger(__name__)
load_dotenv()
GOOGLE_TASKS_MCP_SERVER_PORT = int(os.getenv("GOOGLE_TASKS_MCP_SERVER_PORT", "5000"))

try:
    from .tools.base import (
        auth_token_context,
        extract_access_token,
        get_auth_token,
        list_task_lists,
        create_task_list,
        get_task_list,
        update_task_list,
        delete_task_list,
        list_tasks,
        create_task,
        get_task,
        update_task,
        delete_task,
        move_task,
        clear_completed_tasks,
    )
except ImportError:
    from tools.base import (
        auth_token_context,
        extract_access_token,
        get_auth_token,
        list_task_lists,
        create_task_list,
        get_task_list,
        update_task_list,
        delete_task_list,
        list_tasks,
        create_task,
        get_task,
        update_task,
        delete_task,
        move_task,
        clear_completed_tasks,
    )



@click.command()
@click.option(
    "--port", default=GOOGLE_TASKS_MCP_SERVER_PORT, help="Port to listen on for HTTP"
)
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
@click.option(
    "--stdio",
    is_flag=True,
    default=False,
    help="Run with stdio transport instead of HTTP",
)
def main(port: int, log_level: str, json_response: bool, stdio: bool) -> int:
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    app = Server("google-tasks-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="google_tasks_list_task_lists",
                description="List all Google Tasks task lists",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of task lists to return (1-100)",
                            "default": 100,
                        },
                        "page_token": {
                            "type": "string",
                            "description": "Token for pagination to get next page of results",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_TASKS_TASK_LIST", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="google_tasks_create_task_list",
                description="Create a new Google Tasks task list",
                inputSchema={
                    "type": "object",
                    "required": ["title"],
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Title of the task list",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_TASKS_TASK_LIST"}
                ),
            ),
            types.Tool(
                name="google_tasks_get_task_list",
                description="Get details of a specific Google Tasks task list",
                inputSchema={
                    "type": "object",
                    "required": ["task_list_id"],
                    "properties": {
                        "task_list_id": {
                            "type": "string",
                            "description": "ID of the task list",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_TASKS_TASK_LIST", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="google_tasks_update_task_list",
                description="Update a Google Tasks task list",
                inputSchema={
                    "type": "object",
                    "required": ["task_list_id", "title"],
                    "properties": {
                        "task_list_id": {
                            "type": "string",
                            "description": "ID of the task list",
                        },
                        "title": {
                            "type": "string",
                            "description": "New title for the task list",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_TASKS_TASK_LIST"}
                ),
            ),
            types.Tool(
                name="google_tasks_delete_task_list",
                description="Delete a Google Tasks task list",
                inputSchema={
                    "type": "object",
                    "required": ["task_list_id"],
                    "properties": {
                        "task_list_id": {
                            "type": "string",
                            "description": "ID of the task list to delete",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_TASKS_TASK_LIST"}
                ),
            ),
            types.Tool(
                name="google_tasks_list_tasks",
                description="List tasks in a Google Tasks task list with comprehensive filtering",
                inputSchema={
                    "type": "object",
                    "required": ["task_list_id"],
                    "properties": {
                        "task_list_id": {
                            "type": "string",
                            "description": "ID of the task list",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of tasks to return (1-100)",
                            "default": 100,
                        },
                        "show_completed": {
                            "type": "boolean",
                            "description": "Include completed tasks",
                            "default": True,
                        },
                        "show_deleted": {
                            "type": "boolean",
                            "description": "Include deleted tasks",
                            "default": False,
                        },
                        "show_hidden": {
                            "type": "boolean",
                            "description": "Include hidden tasks",
                            "default": False,
                        },
                        "page_token": {
                            "type": "string",
                            "description": "Token for pagination to get next page of results",
                        },
                        "completed_max": {
                            "type": "string",
                            "description": "Upper bound for task completion date (RFC 3339 timestamp)",
                        },
                        "completed_min": {
                            "type": "string",
                            "description": "Lower bound for task completion date (RFC 3339 timestamp)",
                        },
                        "due_max": {
                            "type": "string",
                            "description": "Upper bound for task due date (RFC 3339 timestamp)",
                        },
                        "due_min": {
                            "type": "string",
                            "description": "Lower bound for task due date (RFC 3339 timestamp)",
                        },
                        "show_assigned": {
                            "type": "boolean",
                            "description": "Include tasks assigned to current user",
                            "default": False,
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_TASKS_TASK", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="google_tasks_create_task",
                description="Create a new task in a Google Tasks task list",
                inputSchema={
                    "type": "object",
                    "required": ["task_list_id", "title"],
                    "properties": {
                        "task_list_id": {
                            "type": "string",
                            "description": "ID of the task list",
                        },
                        "title": {"type": "string", "description": "Title of the task"},
                        "notes": {
                            "type": "string",
                            "description": "Notes for the task",
                        },
                        "due": {
                            "type": "string",
                            "description": "Due date for the task (RFC 3339 timestamp)",
                        },
                        "parent": {
                            "type": "string",
                            "description": "Parent task ID for subtasks",
                        },
                        "previous": {
                            "type": "string",
                            "description": "Previous sibling task ID for ordering",
                        },
                        "status": {
                            "type": "string",
                            "description": "Task status: 'needsAction' or 'completed'",
                        },
                        "completed": {
                            "type": "string",
                            "description": "Completion date (RFC 3339 timestamp)",
                        },
                        "deleted": {
                            "type": "boolean",
                            "description": "Whether the task is deleted",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "GOOGLE_TASKS_TASK"}),
            ),
            types.Tool(
                name="google_tasks_get_task",
                description="Get details of a specific Google Tasks task",
                inputSchema={
                    "type": "object",
                    "required": ["task_list_id", "task_id"],
                    "properties": {
                        "task_list_id": {
                            "type": "string",
                            "description": "ID of the task list",
                        },
                        "task_id": {"type": "string", "description": "ID of the task"},
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_TASKS_TASK", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="google_tasks_update_task",
                description="Update a Google Tasks task",
                inputSchema={
                    "type": "object",
                    "required": ["task_list_id", "task_id"],
                    "properties": {
                        "task_list_id": {
                            "type": "string",
                            "description": "ID of the task list",
                        },
                        "task_id": {"type": "string", "description": "ID of the task"},
                        "title": {
                            "type": "string",
                            "description": "New title for the task",
                        },
                        "notes": {
                            "type": "string",
                            "description": "New notes for the task",
                        },
                        "due": {
                            "type": "string",
                            "description": "New due date for the task (RFC 3339 timestamp)",
                        },
                        "status": {
                            "type": "string",
                            "description": "New task status: 'needsAction' or 'completed'",
                        },
                        "completed": {
                            "type": "string",
                            "description": "New completion date (RFC 3339 timestamp)",
                        },
                        "deleted": {
                            "type": "boolean",
                            "description": "Whether the task is deleted",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "GOOGLE_TASKS_TASK"}),
            ),
            types.Tool(
                name="google_tasks_delete_task",
                description="Delete a Google Tasks task",
                inputSchema={
                    "type": "object",
                    "required": ["task_list_id", "task_id"],
                    "properties": {
                        "task_list_id": {
                            "type": "string",
                            "description": "ID of the task list",
                        },
                        "task_id": {
                            "type": "string",
                            "description": "ID of the task to delete",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "GOOGLE_TASKS_TASK"}),
            ),
            types.Tool(
                name="google_tasks_move_task",
                description="Move a Google Tasks task to another position or task list",
                inputSchema={
                    "type": "object",
                    "required": ["task_list_id", "task_id"],
                    "properties": {
                        "task_list_id": {
                            "type": "string",
                            "description": "ID of the current task list",
                        },
                        "task_id": {
                            "type": "string",
                            "description": "ID of the task to move",
                        },
                        "parent": {
                            "type": "string",
                            "description": "New parent task ID for subtasks",
                        },
                        "previous": {
                            "type": "string",
                            "description": "New previous sibling task ID for ordering",
                        },
                        "destination_tasklist": {
                            "type": "string",
                            "description": "Destination task list ID for cross-list moves",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "GOOGLE_TASKS_TASK"}),
            ),
            types.Tool(
                name="google_tasks_clear_completed_tasks",
                description="Clear all completed tasks from a Google Tasks task list",
                inputSchema={
                    "type": "object",
                    "required": ["task_list_id"],
                    "properties": {
                        "task_list_id": {
                            "type": "string",
                            "description": "ID of the task list",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "GOOGLE_TASKS_TASK"}),
            ),
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        if name == "google_tasks_list_task_lists":
            max_results = arguments.get("max_results", 100)
            page_token = arguments.get("page_token")
            result = await list_task_lists(max_results, page_token)
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "google_tasks_create_task_list":
            title = arguments.get("title")
            if not title:
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(failure("title parameter is required")),
                    )
                ]
            result = await create_task_list(title)
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "google_tasks_get_task_list":
            task_list_id = arguments.get("task_list_id")
            if not task_list_id:
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(failure("task_list_id parameter is required")),
                    )
                ]
            result = await get_task_list(task_list_id)
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "google_tasks_update_task_list":
            task_list_id = arguments.get("task_list_id")
            title = arguments.get("title")
            if not task_list_id or not title:
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(
                            failure("task_list_id and title parameters are required")
                        ),
                    )
                ]
            result = await update_task_list(task_list_id, title)
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "google_tasks_delete_task_list":
            task_list_id = arguments.get("task_list_id")
            if not task_list_id:
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(failure("task_list_id parameter is required")),
                    )
                ]
            result = await delete_task_list(task_list_id)
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "google_tasks_list_tasks":
            task_list_id = arguments.get("task_list_id")
            if not task_list_id:
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(failure("task_list_id parameter is required")),
                    )
                ]
            max_results = arguments.get("max_results", 100)
            show_completed = arguments.get("show_completed", True)
            show_deleted = arguments.get("show_deleted", False)
            show_hidden = arguments.get("show_hidden", False)
            page_token = arguments.get("page_token")
            completed_max = arguments.get("completed_max")
            completed_min = arguments.get("completed_min")
            due_max = arguments.get("due_max")
            due_min = arguments.get("due_min")
            show_assigned = arguments.get("show_assigned", False)
            result = await list_tasks(
                task_list_id,
                max_results,
                show_completed,
                show_deleted,
                show_hidden,
                page_token,
                completed_max,
                completed_min,
                due_max,
                due_min,
                show_assigned,
            )
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "google_tasks_create_task":
            task_list_id = arguments.get("task_list_id")
            title = arguments.get("title")
            if not task_list_id or not title:
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(
                            failure("task_list_id and title parameters are required")
                        ),
                    )
                ]
            notes = arguments.get("notes")
            due = arguments.get("due")
            parent = arguments.get("parent")
            previous = arguments.get("previous")
            status = arguments.get("status")
            completed = arguments.get("completed")
            deleted = arguments.get("deleted")
            result = await create_task(
                task_list_id,
                title,
                notes,
                due,
                parent,
                previous,
                status,
                completed,
                deleted,
            )
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "google_tasks_get_task":
            task_list_id = arguments.get("task_list_id")
            task_id = arguments.get("task_id")
            if not task_list_id or not task_id:
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(
                            failure("task_list_id and task_id parameters are required")
                        ),
                    )
                ]
            result = await get_task(task_list_id, task_id)
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "google_tasks_update_task":
            task_list_id = arguments.get("task_list_id")
            task_id = arguments.get("task_id")
            if not task_list_id or not task_id:
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(
                            failure("task_list_id and task_id parameters are required")
                        ),
                    )
                ]
            title = arguments.get("title")
            notes = arguments.get("notes")
            due = arguments.get("due")
            status = arguments.get("status")
            completed = arguments.get("completed")
            deleted = arguments.get("deleted")
            result = await update_task(
                task_list_id, task_id, title, notes, due, status, completed, deleted
            )
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "google_tasks_delete_task":
            task_list_id = arguments.get("task_list_id")
            task_id = arguments.get("task_id")
            if not task_list_id or not task_id:
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(
                            failure("task_list_id and task_id parameters are required")
                        ),
                    )
                ]
            result = await delete_task(task_list_id, task_id)
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "google_tasks_move_task":
            task_list_id = arguments.get("task_list_id")
            task_id = arguments.get("task_id")
            if not task_list_id or not task_id:
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(
                            failure("task_list_id and task_id parameters are required")
                        ),
                    )
                ]
            parent = arguments.get("parent")
            previous = arguments.get("previous")
            destination_tasklist = arguments.get("destination_tasklist")
            result = await move_task(
                task_list_id, task_id, parent, previous, destination_tasklist
            )
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "google_tasks_clear_completed_tasks":
            task_list_id = arguments.get("task_list_id")
            if not task_list_id:
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(failure("task_list_id parameter is required")),
                    )
                ]
            result = await clear_completed_tasks(task_list_id)
            return [types.TextContent(type="text", text=json.dumps(result))]
        return [
            types.TextContent(
                type="text",
                text=json.dumps(failure(f"Unknown tool: {name}", code="unknown_tool")),
            )
        ]

    if stdio:
        logger.info("Starting Google Tasks MCP server with stdio transport")
        import asyncio

        async def run_stdio():
            auth_token = extract_access_token(None)
            if not auth_token:
                logger.error("No access token found in AUTH_DATA environment variable")
                return

            token = auth_token_context.set(auth_token)
            try:
                async with stdio_server() as (read_stream, write_stream):
                    await app.run(
                        read_stream, write_stream, app.create_initialization_options()
                    )
            finally:
                auth_token_context.reset(token)

        asyncio.run(run_stdio())
        return 0

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")

        auth_token = extract_access_token(request)

        token = auth_token_context.set(auth_token)
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
        event_store=None,
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        logger.info("Handling StreamableHTTP request")

        auth_token = extract_access_token(scope)

        token = auth_token_context.set(auth_token)
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            auth_token_context.reset(token)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        """Context manager for session manager."""
        async with session_manager.run():
            logger.info("Application started with dual transports!")
            try:
                yield
            finally:
                logger.info("Application shutting down...")

    starlette_app = Starlette(
        debug=True,
        routes=[
            # SSE routes
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
            # StreamableHTTP route
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    logger.info(f"Server starting on port {port} with dual transports:")
    logger.info(f"  - SSE endpoint: http://localhost:{port}/sse")
    logger.info(f"  - StreamableHTTP endpoint: http://localhost:{port}/mcp")

    import uvicorn

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)

    return 0


if __name__ == "__main__":
    main()
