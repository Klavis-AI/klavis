import logging
import contextlib
import json
from collections.abc import AsyncIterator
from tools.helpers import _run_sync
from tools.ratelimit import RateLimiter, TooManyRequests
from tools.task import (
    list_task_lists,
    create_task_list,
    list_tasks,
    create_task,
    update_task,
    delete_task,
    find_task_list,
    find_tasks_by_title,
    delete_task_by_title,
    find_task_list_id_by_title,
)

from dotenv import load_dotenv
import os
# MCP / transports
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

# ASGI app
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send


# =========================
# Environment / Logging
# =========================
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("google-tasks-mcp-server")

MCP_PORT = int(os.getenv("GOOGLE_TASKS_MCP_SERVER_PORT", "5000"))

# Default rate limits (can override via CLI or env)
DEFAULT_RATE_MAX = int(os.getenv("GOOGLE_TASKS_RATE_MAX", "60"))       # calls
DEFAULT_RATE_PERIOD = int(os.getenv("GOOGLE_TASKS_RATE_PERIOD", "60")) # seconds

def main(
    port: int,
    log_level: str,
    json_response: bool,
    rate_max: int,
    rate_period: int,
) -> int:
    # Logging
    logging.getLogger().setLevel(getattr(logging, log_level.upper()))
    logger.info(
        f"Starting Google Tasks MCP server on port {port} | rate={rate_max}/{rate_period}s | json_response={json_response}"
    )

    # MCP server instance
    app = Server("google-tasks-mcp-server")
    limiter = RateLimiter(rate_max, rate_period)

    # ---- tools registry ----
    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="gt_list_task_lists",
                description="List all Google Task lists for the authenticated user.",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="gt_create_task",
                description="Create a task in the specified task list (by id or title).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_list_id":  {"type": "string", "description": "ID of the task list."},
                        "task_list_title":{"type": "string", "description": "Title of the task list."},
                        "title":         {"type": "string", "description": "Task title."},
                        "notes":         {"type": "string", "description": "Optional notes."},
                        "create_list_if_missing": {
                            "type": "boolean",
                            "description": "If true and list_title not found, create the list.",
                            "default": False
                        }
                    },
                    # Require title + (id or title)
                    "allOf": [
                        {"required": ["title"]},
                        {
                            "anyOf": [
                                {"required": ["task_list_id"]},
                                {"required": ["task_list_title"]}
                            ]
                        }
                    ]
                },
            ),
            types.Tool(
                name="gt_list_tasks",
                description="List tasks in a specific Google Task list.",
                inputSchema={
                    "type": "object",
                    "required": ["task_list_id"],
                    "properties": {
                        "task_list_id": {"type": "string", "description": "ID of the task list."}
                    },
                },
            ),
            types.Tool(
                name="gt_create_task",
                description="Create a task in the specified task list (optionally include notes).",
                inputSchema={
                    "type": "object",
                    "required": ["task_list_id", "title"],
                    "properties": {
                        "task_list_id": {"type": "string", "description": "ID of the task list."},
                        "title": {"type": "string", "description": "Task title."},
                        "notes": {"type": "string", "description": "Optional notes for the task."},
                    },
                },
            ),
            types.Tool(
                name="gt_update_task",
                description="Update title, notes, or status of an existing task.",
                inputSchema={
                    "type": "object",
                    "required": ["task_list_id", "task_id"],
                    "properties": {
                        "task_list_id": {"type": "string", "description": "ID of the task list."},
                        "task_id": {"type": "string", "description": "ID of the task to update."},
                        "title": {"type": "string", "description": "New title."},
                        "notes": {"type": "string", "description": "New notes."},
                        "status": {
                            "type": "string",
                            "enum": ["needsAction", "completed"],
                            "description": "New status.",
                        },
                    },
                },
            ),
            types.Tool(
                name="gt_delete_task",
                description="Delete a task from a task list.",
                inputSchema={
                    "type": "object",
                    "required": ["task_list_id", "task_id"],
                    "properties": {
                        "task_list_id": {"type": "string", "description": "ID of the task list."},
                        "task_id": {"type": "string", "description": "ID of the task to delete."},
                    },
                },
            ),
            types.Tool(
                name="gt_find_task_list",
                description="Find task lists by exact title. Returns possible matches with ids.",
                inputSchema={"type":"object","required":["title"],
                    "properties":{"title":{"type":"string"}}},
            ),
            types.Tool(
                name="gt_find_tasks",
                description="Find tasks by title in a list. Returns matches with ids.",
                inputSchema={"type":"object","required":["task_list_id","title"],
                    "properties":{
                        "task_list_id":{"type":"string"},
                        "title":{"type":"string"},
                        "exact":{"type":"boolean","default":True}
                    }},
            ),
            types.Tool(
                name="gt_delete_task_by_title",
                description="Resolve by title then delete. Use strategy: one|first|all.",
                inputSchema={"type":"object","required":["task_list_id","title"],
                    "properties":{
                        "task_list_id":{"type":"string"},
                        "title":{"type":"string"},
                        "strategy":{"type":"string","enum":["one","first","all"],"default":"one"},
                        "exact":{"type":"boolean","default":True}
                    }},
            ),

        ]

    # ---- tool dispatcher ----
    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        # Apply per-tool rate limiting
        try:
            limiter.hit(name)
        except TooManyRequests as e:
            logger.warning(str(e))
            return [types.TextContent(type="text", text=json.dumps({"error": str(e)}))]

        # Dispatch by tool name
        try:
            if name == "gt_list_task_lists":
                result = await _run_sync(list_task_lists)

            elif name == "gt_create_task_list":
                title = arguments.get("title")
                result = await _run_sync(create_task_list, title)

            elif name == "gt_list_tasks":
                task_list_id = arguments.get("task_list_id")
                result = await _run_sync(list_tasks, task_list_id)

            elif name == "gt_create_task":
                task_list_id = arguments.get("task_list_id")
                task_list_title = arguments.get("task_list_title")
                title = arguments.get("title")
                notes = arguments.get("notes", "")
                create_if_missing = bool(arguments.get("create_list_if_missing", False))

                if not task_list_id:
                    if not task_list_title:
                        return [types.TextContent(type="text", text=json.dumps({
                            "error": "Provide task_list_id or task_list_title"
                        }))]
                    task_list_id, meta = find_task_list_id_by_title(task_list_title, create_if_missing)
                    if not task_list_id:
                        return [types.TextContent(type="text", text=json.dumps(meta))]

                result = await _run_sync(create_task, task_list_id, title, notes)
                return [types.TextContent(type="text", text=json.dumps(result))]

            elif name == "gt_update_task":
                task_list_id = arguments.get("task_list_id")
                task_id = arguments.get("task_id")
                title = arguments.get("title")
                notes = arguments.get("notes")
                status = arguments.get("status")
                result = await _run_sync(update_task, task_list_id, task_id, title, notes, status)

            elif name == "gt_delete_task":
                task_list_id = arguments.get("task_list_id")
                task_id = arguments.get("task_id")
                result = await _run_sync(delete_task, task_list_id, task_id)

            elif name == "gt_find_task_list":
                result = await _run_sync(find_task_list, arguments.get("title"))

            elif name == "gt_find_tasks":
                result = await _run_sync(
                    find_tasks_by_title,
                    arguments.get("task_list_id"),
                    arguments.get("title"),
                    arguments.get("exact", True),
                )

            elif name == "gt_delete_task_by_title":
                result = await _run_sync(
                    delete_task_by_title,
                    arguments.get("task_list_id"),
                    arguments.get("title"),
                    arguments.get("strategy", "one"),
                    arguments.get("exact", True),
                )
            else:
                result = {"error": f"Unknown tool: {name}"}

        except Exception as e:
            logger.exception(f"Unhandled error in tool '{name}'")
            result = {"error": f"Unhandled server error: {str(e)}"}

        # Respond as text (JSON string) — matches typical MCP text payloads
        return [types.TextContent(type="text", text=json.dumps(result))]

    # =========================
    # Transports (SSE + StreamableHTTP)
    # =========================
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            await app.run(streams[0], streams[1], app.create_initialization_options())
        return Response()

    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,      # Stateless
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        logger.info("Handling StreamableHTTP request")
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(starlette_app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            logger.info("Application started with dual transports!")
            try:
                yield
            finally:
                logger.info("Application shutting down...")

    starlette_app = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
            Mount("/mcp/", app=handle_streamable_http),
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
    import sys
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=MCP_PORT)
    parser.add_argument("--log-level", type=str, default="INFO")
    parser.add_argument("--json-response", action="store_true")
    parser.add_argument("--rate-max", type=int, default=DEFAULT_RATE_MAX)
    parser.add_argument("--rate-period", type=int, default=DEFAULT_RATE_PERIOD)
    args = parser.parse_args()

    main(
        port=args.port,
        log_level=args.log_level,
        json_response=args.json_response,
        rate_max=args.rate_max,
        rate_period=args.rate_period,
    )

