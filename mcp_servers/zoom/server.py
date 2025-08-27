import os
import json
import logging
import contextlib
from collections.abc import AsyncIterator
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

import uvicorn

from tools import (
    zoom_access_token_context,
    validate_access_token,
)

from list import get_tool_list
from call import call_tool

logger = logging.getLogger("zoom-mcp-server")
logging.basicConfig(level=logging.INFO)



class ZoomMCPServer:
    """Zoom MCP Server with organized tool management."""
    
    def __init__(self):
        self.server = Server("zoom-mcp-server")
        self._register_handlers()
    
    def _register_handlers(self):
        """Register the tool list and call handlers with the MCP server."""
        
        @self.server.list_tools()
        async def list_tools() -> list[types.Tool]:
            return get_tool_list()

        @self.server.call_tool()
        async def call_tool_handler(name: str, arguments: Dict[str, Any]) -> list[types.TextContent]:
            return await call_tool(name, arguments)


@click.command()
@click.option("--port", default=5000, help="Port to listen on for HTTP")
@click.option("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
@click.option("--json-response", is_flag=True, default=True, help="Enable JSON responses for StreamableHTTP")
def main(port: int, log_level: str, json_response: bool) -> int:
    """Zoom MCP server with SSE + StreamableHTTP transports using OAuth access tokens."""
    logging.getLogger().setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Initialize the Zoom MCP server
    zoom_server = ZoomMCPServer()
    app = zoom_server.server

    # ------------------------------- Transports ------------------------------#
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        """
        SSE transport endpoint.
        Requires 'x-zoom-access-token' header for OAuth authentication.
        """
        logger.info("Handling SSE connection")
        
        # Extract OAuth access token
        access_token = request.headers.get("x-zoom-access-token")
        
        # Validate required header
        if not access_token:
            logger.error("Missing OAuth access token header")
            return Response(
                content="Missing required authentication header: x-zoom-access-token",
                status_code=401
            )
        
        # Validate access token
        if not await validate_access_token(access_token):
            logger.error("Invalid OAuth access token")
            return Response(
                content="Invalid OAuth access token",
                status_code=401
            )
        
        # Set context variable for this request
        token_context = zoom_access_token_context.set(access_token)

        try:
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
                await app.run(streams[0], streams[1], app.create_initialization_options())
        finally:
            # Clean up context variable
            zoom_access_token_context.reset(token_context)
        return Response()

    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        """
        Streamable HTTP transport endpoint.
        Requires 'x-zoom-access-token' header for OAuth authentication.
        """
        logger.info("Handling StreamableHTTP request")
        headers = {k.decode("utf-8"): v.decode("utf-8") for k, v in scope.get("headers", [])}
        
        # Extract OAuth access token
        access_token = headers.get("x-zoom-access-token")
        
        # Validate required header
        if not access_token:
            logger.error("Missing OAuth access token header")
            # Send error response
            error_response = {
                "error": "Missing OAuth access token",
                "message": "Please provide x-zoom-access-token header"
            }
            await send({
                "type": "http.response.start",
                "status": 401,
                "headers": [(b"content-type", b"application/json")]
            })
            await send({
                "type": "http.response.body",
                "body": json.dumps(error_response).encode()
            })
            return
        
        # Validate access token
        if not await validate_access_token(access_token):
            logger.error("Invalid OAuth access token")
            # Send error response
            error_response = {
                "error": "Invalid OAuth access token",
                "message": "The provided OAuth access token is invalid or expired"
            }
            await send({
                "type": "http.response.start",
                "status": 401,
                "headers": [(b"content-type", b"application/json")]
            })
            await send({
                "type": "http.response.body",
                "body": json.dumps(error_response).encode()
            })
            return
        
        # Set context variable for this request
        token_context = zoom_access_token_context.set(access_token)
            
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            # Clean up context variable
            zoom_access_token_context.reset(token_context)

    @contextlib.asynccontextmanager
    async def lifespan(_app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            logger.info("Application started with dual transports!")
            logger.info("OAuth authentication required: x-zoom-access-token")
            try:
                yield
            finally:
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
    logger.info("  - OAuth authentication required for all endpoints")

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)

    return 0


if __name__ == "__main__":

    exit(main())
