# mcp_servers/amplitude/server.py
from __future__ import annotations

import base64
import contextlib
import json
import logging
import os
from collections.abc import AsyncIterator
from contextvars import ContextVar
from typing import Any

import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

# per-request creds (fallback to env)
amplitude_api_key_ctx: ContextVar[str] = ContextVar("amplitude_api_key", default=os.getenv("AMPLITUDE_API_KEY", ""))
amplitude_api_secret_ctx: ContextVar[str] = ContextVar("amplitude_api_secret", default=os.getenv("AMPLITUDE_API_SECRET", ""))

# tools (they should read creds via contextvars or env)
from tools.track_events import track_event as run_track_event
from tools.identify_user import identify_user as run_identify_user
from tools.get_user_profile import get_user_profile as run_get_user_profile
from tools.list_event_categories import list_event_categories as run_list_event_categories

logger = logging.getLogger(__name__)
PORT_DEFAULT = int(os.getenv("AMPLITUDE_MCP_SERVER_PORT", "5000"))

def _extract_auth(request_or_scope) -> tuple[str, str]:
    """Read base64(JSON) from x-auth-data header and return (api_key, api_secret)."""
    raw = None
    if hasattr(request_or_scope, "headers"):
        raw = request_or_scope.headers.get(b"x-auth-data") or request_or_scope.headers.get("x-auth-data")
    elif isinstance(request_or_scope, dict) and "headers" in request_or_scope:
        hdrs = dict(request_or_scope.get("headers", []))
        raw = hdrs.get(b"x-auth-data") or hdrs.get("x-auth-data")
    if not raw:
        return "", ""
    try:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        payload = base64.b64decode(raw).decode("utf-8")
        obj = json.loads(payload)
        api_key = obj.get("api_key") or obj.get("AMPLITUDE_API_KEY") or ""
        api_secret = obj.get("api_secret") or obj.get("AMPLITUDE_API_SECRET") or ""
        return api_key, api_secret
    except Exception as e:
        logger.warning(f"bad x-auth-data: {e}")
        return "", ""

@click.command()
@click.option("--port", default=PORT_DEFAULT, help="HTTP port for SSE/StreamableHTTP")
@click.option("--log-level", default="INFO", help="DEBUG|INFO|WARNING|ERROR|CRITICAL")
@click.option("--json-response", is_flag=True, default=False, help="Return JSON for StreamableHTTP")
def main(port: int, log_level: str, json_response: bool) -> int:
    logging.basicConfig(level=getattr(logging, log_level.upper(), logging.INFO),
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    app = Server("amplitude-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="amplitude_track_event",
                description="Send one event to Amplitude HTTP V2. Requires event_type and one of user_id/device_id.",
                inputSchema={
                    "type": "object",
                    "required": ["event_type"],
                    "properties": {
                        "event_type": {"type": "string"},
                        "user_id": {"type": "string"},
                        "device_id": {"type": "string"},
                        "event_properties": {"type": ["object", "string"], "additionalProperties": True},
                        "time": {"type": ["integer", "number"], "description": "ms (seconds auto-converted)"},
                    },
                },
            ),
            types.Tool(
                name="amplitude_identify_user",
                description="Identify user / set user properties via Identify API (form-encoded).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "device_id": {"type": "string"},
                        "user_properties": {"type": "object", "additionalProperties": True},
                        "operations": {"type": "object", "additionalProperties": True}
                    },
                },
            ),
            types.Tool(
                name="amplitude_get_user_profile",
                description="Fetch user profile (may be plan/region gated).",
                inputSchema={
                    "type": "object",
                    "required": ["user_id"],
                    "properties": {
                        "user_id": {"type": "string"},
                        "get_amp_props": {"type": "boolean", "default": False},
                        "get_cohort_ids": {"type": "boolean", "default": False},
                        "get_recs": {"type": "boolean", "default": False},
                        "get_computations": {"type": "boolean", "default": False},
                    },
                },
            ),
            types.Tool(
                name="amplitude_list_event_categories",
                description="List taxonomy categories (may be gated).",
                inputSchema={"type": "object", "properties": {}},
            ),
        ]

    @app.call_tool()
    async def call_tool(name: str, args: dict) -> list[types.TextContent]:
        try:
            if name == "amplitude_track_event":
                res = run_track_event(
                    event_type=args.get("event_type"),
                    user_id=args.get("user_id"),
                    device_id=args.get("device_id"),
                    event_properties=args.get("event_properties"),
                    time=args.get("time"),
                )
            elif name == "amplitude_identify_user":
                res = run_identify_user(
                    user_id=args.get("user_id"),
                    device_id=args.get("device_id"),
                    user_properties=args.get("user_properties"),
                    operations=args.get("operations"),
                )
            elif name == "amplitude_get_user_profile":
                res = run_get_user_profile(
                    user_id=args.get("user_id"),
                    get_amp_props=args.get("get_amp_props", False),
                    get_cohort_ids=args.get("get_cohort_ids", False),
                    get_recs=args.get("get_recs", False),
                    get_computations=args.get("get_computations", False),
                )
            elif name == "amplitude_list_event_categories":
                res = run_list_event_categories()
            else:
                return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
        except Exception as e:
            logger.exception(f"tool error: {name}")
            return [types.TextContent(type="text", text=f"Error: {e}")]
        return [types.TextContent(type="text", text=json.dumps(res, indent=2, ensure_ascii=False))]

    # SSE
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        api_key, api_secret = _extract_auth(request)
        tok1 = amplitude_api_key_ctx.set(api_key or amplitude_api_key_ctx.get())
        tok2 = amplitude_api_secret_ctx.set(api_secret or amplitude_api_secret_ctx.get())
        try:
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
                await app.run(streams[0], streams[1], app.create_initialization_options())
        finally:
            amplitude_api_key_ctx.reset(tok1)
            amplitude_api_secret_ctx.reset(tok2)
        return Response()

    # StreamableHTTP
    session_manager = StreamableHTTPSessionManager(app=app, event_store=None, json_response=json_response, stateless=True)

    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        api_key, api_secret = _extract_auth(scope)
        tok1 = amplitude_api_key_ctx.set(api_key or amplitude_api_key_ctx.get())
        tok2 = amplitude_api_secret_ctx.set(api_secret or amplitude_api_secret_ctx.get())
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            amplitude_api_key_ctx.reset(tok1)
            amplitude_api_secret_ctx.reset(tok2)

    @contextlib.asynccontextmanager
    async def lifespan(starlette_app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            logger.info("Amplitude MCP server started")
            yield

    star = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    logger.info(f"Serving on :{port} (SSE /mcp)")
    import uvicorn
    uvicorn.run(star, host="0.0.0.0", port=port)
    return 0

if __name__ == "__main__":
    main()