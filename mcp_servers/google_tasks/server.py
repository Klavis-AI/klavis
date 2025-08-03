import os
import json
import time
import logging
import contextlib
import asyncio
from collections import defaultdict, deque
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional

import click
from dotenv import load_dotenv

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

# Google Tasks
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# =========================
# Environment / Logging
# =========================
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("google-tasks-mcp-server")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")

if not (GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET and GOOGLE_REFRESH_TOKEN):
    raise ValueError(
        "Missing Google OAuth env vars. Required: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN."
    )

MCP_PORT = int(os.getenv("GOOGLE_TASKS_MCP_SERVER_PORT", "5000"))

# Default rate limits (can override via CLI or env)
DEFAULT_RATE_MAX = int(os.getenv("GOOGLE_TASKS_RATE_MAX", "60"))       # calls
DEFAULT_RATE_PERIOD = int(os.getenv("GOOGLE_TASKS_RATE_PERIOD", "60")) # seconds


# =========================
# Helpers
# =========================
def _get_service():
    """Build a Google Tasks API service using refresh token flow."""
    creds = Credentials(
        None,
        refresh_token=GOOGLE_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
    )
    return build("tasks", "v1", credentials=creds)

def _error_from_http(e: HttpError, default_msg: str) -> Dict[str, Any]:
    """Normalize Google API errors."""
    status = getattr(e, "resp", None).status if getattr(e, "resp", None) else None
    try:
        body = e.error_details if hasattr(e, "error_details") else None
    except Exception:
        body = None
    if status in (403, 429):
        return {"error": "Rate limit exceeded or unauthorized.", "status": status}
    return {"error": f"{default_msg} (HTTP {status})", "status": status, "details": str(e)}

async def _run_sync(fn, *args, **kwargs):
    """Run blocking Google client calls in a thread."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))


# =========================
# Atomic functions (sync)
# =========================
def list_task_lists() -> List[Dict[str, Any]]:
    try:
        service = _get_service()
        result = service.tasklists().list(maxResults=50).execute()
        return result.get("items", [])
    except HttpError as e:
        logger.exception("Error listing task lists")
        return _error_from_http(e, "Failed to list task lists")

def create_task_list(title: str) -> Dict[str, Any]:
    try:
        service = _get_service()
        return service.tasklists().insert(body={"title": title}).execute()
    except HttpError as e:
        logger.exception("Error creating task list")
        return _error_from_http(e, "Failed to create task list")

def list_tasks(task_list_id: str) -> List[Dict[str, Any]]:
    try:
        service = _get_service()
        result = service.tasks().list(tasklist=task_list_id).execute()
        return result.get("items", [])
    except HttpError as e:
        logger.exception("Error listing tasks")
        return _error_from_http(e, "Failed to list tasks")

def create_task(task_list_id: str, title: str, notes: str = "") -> Dict[str, Any]:
    try:
        service = _get_service()
        return service.tasks().insert(tasklist=task_list_id, body={"title": title, "notes": notes}).execute()
    except HttpError as e:
        logger.exception("Error creating task")
        return _error_from_http(e, "Failed to create task")

def update_task(
    task_list_id: str,
    task_id: str,
    title: Optional[str] = None,
    notes: Optional[str] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    try:
        service = _get_service()
        existing = service.tasks().get(tasklist=task_list_id, task=task_id).execute()
        if title is not None:
            existing["title"] = title
        if notes is not None:
            existing["notes"] = notes
        if status is not None:
            existing["status"] = status  # 'needsAction' or 'completed'
        return service.tasks().update(tasklist=task_list_id, task=task_id, body=existing).execute()
    except HttpError as e:
        logger.exception("Error updating task")
        return _error_from_http(e, "Failed to update task")

def delete_task(task_list_id: str, task_id: str) -> Dict[str, Any]:
    try:
        service = _get_service()
        service.tasks().delete(tasklist=task_list_id, task=task_id).execute()
        return {"status": "deleted"}
    except HttpError as e:
        logger.exception("Error deleting task")
        return _error_from_http(e, "Failed to delete task")


# =========================
# Simple per-tool rate limiter
# =========================
class TooManyRequests(Exception):
    pass

class RateLimiter:
    def __init__(self, max_calls: int, period_seconds: int):
        self.max = max_calls
        self.period = period_seconds
        self.calls = defaultdict(deque)  # key -> deque[timestamps]

    def hit(self, key: str):
        now = time.monotonic()
        dq = self.calls[key]
        # purge old calls
        while dq and (now - dq[0]) > self.period:
            dq.popleft()
        if len(dq) >= self.max:
            raise TooManyRequests(f"Rate limit exceeded for '{key}': {self.max} calls per {self.period}s.")
        dq.append(now)


# =========================
# CLI / Server
# =========================
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
                name="gt_create_task_list",
                description="Create a new Google Task list with the given title.",
                inputSchema={
                    "type": "object",
                    "required": ["title"],
                    "properties": {
                        "title": {"type": "string", "description": "Title for the new task list."}
                    },
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
                title = arguments.get("title")
                notes = arguments.get("notes", "")
                result = await _run_sync(create_task, task_list_id, title, notes)

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

