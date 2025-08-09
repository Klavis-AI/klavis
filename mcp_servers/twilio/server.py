import contextlib
import logging
import os
import json
import asyncio
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
    send_sms,
    send_mms,
    list_messages,
    get_message_details,
    redact_message,
    list_phone_numbers
)

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

TWILIO_MCP_SERVER_PORT = int(os.getenv("TWILIO_MCP_SERVER_PORT", "5000"))

@click.command()
@click.option("--port", default=TWILIO_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("twilio-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            # SMS
            types.Tool(
                name="twilio_send_sms",
                description="Send an SMS message using Twilio.",
                inputSchema={
                    "type": "object",
                    "required": ["to", "body"],
                    "properties": {
                        "to": {
                            "type": "string",
                            "description": "The phone number to send the SMS to (e.g., +1234567890).",
                        },
                        "body": {
                            "type": "string",
                            "description": "The message body to send.",
                        },
                    },
                },
            ),
            # MMS
            types.Tool(
                name="twilio_send_mms",
                description="Send an MMS message with media using Twilio.",
                inputSchema={
                    "type": "object",
                    "required": ["to", "media_url"],
                    "properties": {
                        "to": {
                            "type": "string",
                            "description": "The phone number to send the MMS to (e.g., +1234567890).",
                        },
                        "media_url": {
                            "type": "string",
                            "description": "The URL of the media to send.",
                        },
                        "body": {
                            "type": "string",
                            "description": "Optional message body to accompany the media.",
                        },
                    },
                },
            ),
            # List Messages
            types.Tool(
                name="twilio_list_messages",
                description="List recent messages from Twilio account.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of messages to retrieve (default: 20, max: 100).",
                        },
                    },
                },
            ),
            # Get Message Details
            types.Tool(
                name="twilio_get_message_details",
                description="Get detailed information about a specific message.",
                inputSchema={
                    "type": "object",
                    "required": ["sid"],
                    "properties": {
                        "sid": {
                            "type": "string",
                            "description": "The SID of the message to retrieve details for.",
                        },
                    },
                },
            ),
            # Redact Message
            types.Tool(
                name="twilio_redact_message",
                description="Redact (clear the body of) a message in Twilio.",
                inputSchema={
                    "type": "object",
                    "required": ["sid"],
                    "properties": {
                        "sid": {
                            "type": "string",
                            "description": "The SID of the message to redact.",
                        },
                    },
                },
            ),
            # List Phone Numbers
            types.Tool(
                name="twilio_list_phone_numbers",
                description="List phone numbers available in the Twilio account.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        
        # SMS
        if name == "twilio_send_sms":
            try:
                result = await send_sms(arguments["to"], arguments["body"])
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
        
        # MMS
        elif name == "twilio_send_mms":
            try:
                body = arguments.get("body", "")
                result = await send_mms(arguments["to"], arguments["media_url"], body)
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
        
        # List Messages
        elif name == "twilio_list_messages":
            try:
                limit = arguments.get("limit", 20)
                result = await list_messages(limit)
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
        
        # Get Message Details
        elif name == "twilio_get_message_details":
            try:
                result = await get_message_details(arguments["sid"])
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
        
        # Redact Message
        elif name == "twilio_redact_message":
            try:
                result = await redact_message(arguments["sid"])
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
        
        # List Phone Numbers
        elif name == "twilio_list_phone_numbers":
            try:
                result = await list_phone_numbers()
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
            raise ValueError(f"Unknown tool: {name}")

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
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
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        """Handle StreamableHTTP transport."""
        # Extract auth token from headers (allow None - will be handled at tool level)
        auth_token = None
        for name, value in scope.get("headers", []):
            if name == b"x-auth-token":
                auth_token = value.decode("utf-8")
                break
        
        # Set the auth token in context for this request (can be None/empty)
        token = auth_token_context.set(auth_token or "")
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

    logger.info(f"Server starting on port {port} with dual transports:")
    logger.info(f"  - SSE endpoint: http://localhost:{port}/sse")
    logger.info(f"  - StreamableHTTP endpoint: http://localhost:{port}/mcp")

    # Run the server
    import uvicorn
    uvicorn.run(starlette_app, host="0.0.0.0", port=port)

    return 0

if __name__ == "__main__":
    main() 