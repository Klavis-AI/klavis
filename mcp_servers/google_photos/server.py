from tools.picker import (
    google_photos_create_picker_session,
    google_photos_get_picker_session,
    google_photos_list_picked_media_items,
    google_photos_delete_picker_session
)
import os
import json
import logging
import contextlib
import uvicorn
import click
import asyncio
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional
from contextvars import ContextVar
from enum import Enum

import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

GOOGLE_PHOTOS_MCP_SERVER_PORT = int(os.getenv("GOOGLE_PHOTOS_MCP_SERVER_PORT", "5001"))

# Context variable to store the access token for each request
auth_token_context: ContextVar[str] = ContextVar('auth_token')

GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")


@click.command()
@click.option("--port", default=GOOGLE_PHOTOS_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Validate required OAuth credentials at startup
    if not all([GOOGLE_REFRESH_TOKEN, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET]):
        missing = []
        if not GOOGLE_REFRESH_TOKEN:
            missing.append("GOOGLE_REFRESH_TOKEN")
        if not GOOGLE_CLIENT_ID:
            missing.append("GOOGLE_CLIENT_ID")
        if not GOOGLE_CLIENT_SECRET:
            missing.append("GOOGLE_CLIENT_SECRET")
        
        logger.error(f"Missing required OAuth credentials: {', '.join(missing)}")
        logger.error("Please set the following environment variables or add them to your .env file:")
        for var in missing:
            logger.error(f"  {var}")
        return 1

    # Create the MCP server instance
    app = Server("google-photos-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            # Picker API tools
            types.Tool(
                name="google_photos_create_picker_session",
                description="Create a new picker session for user photo selection from Google Photos",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            types.Tool(
                name="google_photos_get_picker_session",
                description="Get the status of a picker session",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "sessionId": {
                            "type": "string",
                            "description": "ID of the picker session"
                        }
                    },
                    "required": ["sessionId"]
                }
            ),
            types.Tool(
                name="google_photos_list_picked_media_items",
                description="List media items picked by the user in a session",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "sessionId": {
                            "type": "string",
                            "description": "ID of the picker session"
                        },
                        "pageSize": {
                            "type": "integer",
                            "description": "Number of items to return (max 100)",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 50
                        },
                        "pageToken": {
                            "type": "string",
                            "description": "Token for pagination"
                        }
                    },
                    "required": ["sessionId"]
                }
            ),
            types.Tool(
                name="google_photos_delete_picker_session",
                description="Delete a picker session",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "sessionId": {
                            "type": "string",
                            "description": "ID of the picker session to delete"
                        }
                    },
                    "required": ["sessionId"]
                }
            )
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        token = auth_token_context.set(arguments.get("access_token", ""))
        try:
            if name == "google_photos_create_picker_session":
                result = await google_photos_create_picker_session(arguments.get("access_token", ""))
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

            elif name == "google_photos_get_picker_session":
                result = await google_photos_get_picker_session(arguments.get("access_token", ""), arguments["sessionId"])
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

            elif name == "google_photos_list_picked_media_items":
                result = await google_photos_list_picked_media_items(
                    arguments.get("access_token", ""),
                    arguments["sessionId"],
                    arguments.get("pageSize", 50),
                    arguments.get("pageToken")
                )
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

            elif name == "google_photos_delete_picker_session":
                result = await google_photos_delete_picker_session(arguments.get("access_token", ""), arguments["sessionId"])
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

            else:
                raise ValueError(f"Unknown tool: {name}")
        finally:
            auth_token_context.reset(token)

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")

        auth_token = request.headers.get('x-auth-token')
        token = auth_token_context.set(auth_token or "")
        try:
            async for message in sse.handle_post_message(request):
                yield message
        finally:
            auth_token_context.reset(token)

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

        headers = dict(scope.get("headers", []))
        auth_token = headers.get(b'x-auth-token')
        if auth_token:
            auth_token = auth_token.decode('utf-8')

        token = auth_token_context.set(auth_token or "")
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            auth_token_context.reset(token)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            yield

    # Create an ASGI application with routes for both transports
    starlette_app = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    logger.info(f"Google Photos MCP Server starting on port {port}")
    logger.info(f"  - SSE endpoint: http://localhost:{port}/sse")
    logger.info(f"  - StreamableHTTP endpoint: http://localhost:{port}/mcp")
    logger.info("  - Uses Picker API for user photo selection")
    logger.info("  - Library API limited to app-created content")

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)

    return 0

if __name__ == "__main__":
    main()