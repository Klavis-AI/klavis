import contextlib
import logging
import os
import json
from typing import Any, Dict

import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from dotenv import load_dotenv

from tools import auth_token_context
from utils import list_tools, call_tool

logger = logging.getLogger(__name__)

load_dotenv()

SERVER_PORT = int(os.getenv("SERVER_PORT", "5000"))



@click.command()
@click.option("--port", default=SERVER_PORT, help="Port to listen on for HTTP")
@click.option("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
@click.option("--json-response", is_flag=True, default=False, help="Enable JSON responses for StreamableHTTP instead of SSE streams")
def main(port: int, log_level: str, json_response: bool) -> int:
    # Set up basic logging so we can see what's happening at the level we choose.
    logging.basicConfig(level=getattr(logging, log_level.upper()), format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # This is the core MCP server object that handles tool listing and calls.
    app = Server("google-meet-mcp-server")

    app.list_tools()(list_tools)
    app.call_tool()(call_tool)

    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        # For SSE requests, we grab the token from headers, set it in context, and run the app with SSE transport.
        auth_token = request.headers.get('x-auth-token')
        token = auth_token_context.set(auth_token or "")
        try:
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
                await app.run(streams[0], streams[1], app.create_initialization_options())
        finally:
            auth_token_context.reset(token)
        return Response()

    session_manager = StreamableHTTPSessionManager(app=app, event_store=None, json_response=json_response, stateless=True)

    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        # Similar to SSE, but for HTTP: extract token from headers, set context, and handle the request.
        headers = scope.get("headers", [])
        auth_token = next((v.decode('utf-8') for k, v in headers if k == b'x-auth-token'), None)
        token = auth_token_context.set(auth_token or "")
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            auth_token_context.reset(token)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette):
        # This manages the app's lifetime: starts the session manager, logs startup, yields control, then shuts down.
        async with session_manager.run():
            logger.info("Application started with dual transports!")
            yield
            logger.info("Application shutting down...")

    starlette_app = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
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
