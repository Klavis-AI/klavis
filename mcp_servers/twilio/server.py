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
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
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

TWILIO_MCP_SERVER_PORT = int(os.getenv("TWILIO_MCP_SERVER_PORT", "5001"))

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
            result = await send_sms(arguments["to"], arguments["body"])
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        # MMS
        elif name == "twilio_send_mms":
            body = arguments.get("body", "")
            result = await send_mms(arguments["to"], arguments["media_url"], body)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        # List Messages
        elif name == "twilio_list_messages":
            limit = arguments.get("limit", 20)
            result = await list_messages(limit)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        # Get Message Details
        elif name == "twilio_get_message_details":
            result = await get_message_details(arguments["sid"])
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        # Redact Message
        elif name == "twilio_redact_message":
            result = await redact_message(arguments["sid"])
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        # List Phone Numbers
        elif name == "twilio_list_phone_numbers":
            result = await list_phone_numbers()
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        else:
            raise ValueError(f"Unknown tool: {name}")

    # Create Starlette app for HTTP transport
    starlette_app = Starlette()

    @starlette_app.middleware("http")
    async def auth_middleware(request, call_next):
        """Extract auth token from headers and set in context."""
        auth_token = request.headers.get("x-auth-token")
        if auth_token:
            auth_token_context.set(auth_token)
        else:
            # For Twilio, we'll use environment variables as fallback
            auth_token_context.set("env")
        
        response = await call_next(request)
        return response

    async def handle_http_request(request):
        """Handle HTTP requests for MCP tool calls."""
        try:
            # Parse the JSON request
            data = await request.json()
            
            # Extract the tool call information
            method = data.get("method")
            params = data.get("params", {})
            
            if method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                # Call the appropriate tool
                if tool_name == "twilio_send_sms":
                    result = await send_sms(arguments["to"], arguments["body"])
                elif tool_name == "twilio_send_mms":
                    body = arguments.get("body", "")
                    result = await send_mms(arguments["to"], arguments["media_url"], body)
                elif tool_name == "twilio_list_messages":
                    limit = arguments.get("limit", 20)
                    result = await list_messages(limit)
                elif tool_name == "twilio_get_message_details":
                    result = await get_message_details(arguments["sid"])
                elif tool_name == "twilio_redact_message":
                    result = await redact_message(arguments["sid"])
                elif tool_name == "twilio_list_phone_numbers":
                    result = await list_phone_numbers()
                else:
                    return Response(
                        json.dumps({"error": f"Unknown tool: {tool_name}"}),
                        status_code=400,
                        media_type="application/json"
                    )
                
                # Return the result
                return Response(
                    json.dumps({
                        "jsonrpc": "2.0",
                        "id": data.get("id", 1),
                        "result": result
                    }),
                    media_type="application/json"
                )
            else:
                return Response(
                    json.dumps({"error": f"Unknown method: {method}"}),
                    status_code=400,
                    media_type="application/json"
                )
                
        except Exception as e:
            return Response(
                json.dumps({
                    "jsonrpc": "2.0",
                    "id": data.get("id", 1) if 'data' in locals() else 1,
                    "error": {"message": str(e)}
                }),
                status_code=500,
                media_type="application/json"
            )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        """Handle StreamableHTTP transport."""
        async with StreamableHTTPSessionManager(
            scope, receive, send, json_response=json_response
        ) as session:
            await session.run_session(app)

    # Add routes
    starlette_app.add_route("/http", handle_http_request, methods=["POST"])
    starlette_app.add_route("/streamable", handle_streamable_http)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        # Startup
        logger.info(f"Starting Twilio MCP server on port {port}")
        yield
        # Shutdown
        logger.info("Shutting down Twilio MCP server")

    starlette_app.router.lifespan_context = lifespan

    # Run the server
    import uvicorn
    uvicorn.run(starlette_app, host="0.0.0.0", port=port)

    return 0

if __name__ == "__main__":
    main() 