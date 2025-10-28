import contextlib
import logging
import os
import json
from collections.abc import AsyncIterator
from typing import Any, Dict
from contextvars import ContextVar

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

from tools import (
    auth_token_context,
    perplexity_search,
    perplexity_reason,
)

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

PERPLEXITY_MCP_SERVER_PORT = int(os.getenv("PERPLEXITY_MCP_SERVER_PORT", "5000"))

@click.command()
@click.option("--port", default=PERPLEXITY_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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

    # Create the MCP server instance
    app = Server("perplexity-ai-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            # Perplexity Search Tool
            types.Tool(
                name="perplexity_search",
                description=(
                    "Performs web search using the Sonar API. "
                    "Accepts an array of messages (each with a role and content) "
                    "and returns a search completion response from the Perplexity model."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "messages": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "role": {
                                        "type": "string",
                                        "description": "Role of the message (e.g., system, user, assistant)",
                                    },
                                    "content": {
                                        "type": "string",
                                        "description": "The content of the message",
                                    },
                                },
                                "required": ["role", "content"],
                            },
                            "description": "Array of conversation messages",
                        },
                    },
                    "required": ["messages"],
                },
            ),
            # Perplexity Reason Tool
            types.Tool(
                name="perplexity_reason",
                description=(
                    "Performs reasoning tasks using the Sonar API. "
                    "Accepts an array of messages (each with a role and content) "
                    "and returns a well‑reasoned response using the sonar‑reasoning‑pro model."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "messages": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "role": {
                                        "type": "string",
                                        "description": "Role of the message (e.g., system, user, assistant)",
                                    },
                                    "content": {
                                        "type": "string",
                                        "description": "The content of the message",
                                    },
                                },
                                "required": ["role", "content"],
                            },
                            "description": "Array of conversation messages",
                        },
                    },
                    "required": ["messages"],
                },
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        
        try:
            if name == "perplexity_search":
                messages = arguments.get("messages")
                if not messages or not isinstance(messages, list):
                    return [types.TextContent(type="text", text="Error: 'messages' parameter is required and must be an array")]
                
                result = await perplexity_search(messages)
                return [types.TextContent(type="text", text=result)]

            elif name == "perplexity_reason":
                messages = arguments.get("messages")
                if not messages or not isinstance(messages, list):
                    return [types.TextContent(type="text", text="Error: 'messages' parameter is required and must be an array")]
                
                result = await perplexity_reason(messages)
                return [types.TextContent(type="text", text=result)]
            
            else:
                return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
                
        except Exception as e:
            logger.exception(f"Error executing tool {name}: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        
        # Extract API key from headers (allow None - will be handled at tool level)
        api_key = request.headers.get('x-api-key')
        
        # Set the API key in context for this request (can be None)
        token = auth_token_context.set(api_key or "")
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
        logger.info("Handling StreamableHTTP request")
        
        # Extract API key from headers (allow None - will be handled at tool level)
        headers = dict(scope.get("headers", []))
        api_key = headers.get(b'x-api-key')
        if api_key:
            api_key = api_key.decode('utf-8')
        
        # Set the API key in context for this request (can be None/empty)
        token = auth_token_context.set(api_key or "")
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            auth_token_context.reset(token)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        """Context manager for session manager."""
        async with session_manager.run():
            logger.info("Perplexity AI MCP Server started with dual transports!")
            try:
                yield
            finally:
                logger.info("Perplexity AI MCP Server shutting down...")

    # Create an ASGI application with routes for both transports
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

    logger.info(f"Perplexity AI MCP Server starting on port {port} with dual transports:")
    logger.info(f"  - SSE endpoint: http://localhost:{port}/sse")
    logger.info(f"  - StreamableHTTP endpoint: http://localhost:{port}/mcp")

    import uvicorn

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)

    return 0

if __name__ == "__main__":
    main()
