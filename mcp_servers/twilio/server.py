import contextlib
import logging
import os
import json
import asyncio
from collections.abc import AsyncIterator
from typing import Any, Dict

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

from tools import (
    auth_token_context,
    # Messaging
    twilio_send_sms,
    twilio_send_mms,
    twilio_get_messages,
    twilio_get_message_by_sid,
    # Voice
    twilio_make_call,
    twilio_get_calls,
    twilio_get_call_by_sid,
    twilio_get_recordings,
    # Phone Numbers
    twilio_search_available_numbers,
    twilio_purchase_phone_number,
    twilio_list_phone_numbers,
    twilio_update_phone_number,
    twilio_release_phone_number,
    # Account
    twilio_get_account_info,
    twilio_get_usage_records,
    twilio_get_balance,
)

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

TWILIO_MCP_SERVER_PORT = int(os.getenv("TWILIO_MCP_SERVER_PORT", "5000"))

def get_all_tools() -> list[types.Tool]:
    """Get all tool definitions to avoid duplication between stdio and HTTP modes."""
    return [
        # Messaging Tools
        types.Tool(
            name="twilio_send_sms",
            description="Send an SMS message to a phone number using Twilio. Perfect for sending text notifications, alerts, or confirmations to users.",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient phone number in E.164 format (e.g., +1234567890)"
                    },
                    "from_": {
                        "type": "string", 
                        "description": "Sender phone number (must be a Twilio phone number you own)"
                    },
                    "body": {
                        "type": "string",
                        "description": "Message content (up to 1600 characters)"
                    },
                    "status_callback": {
                        "type": "string",
                        "description": "Optional webhook URL to receive delivery status updates"
                    }
                },
                "required": ["to", "from_", "body"]
            },
            annotations=types.ToolAnnotations(**{"category": "TWILIO_MESSAGING"}),
        ),
        types.Tool(
            name="twilio_send_mms",
            description="Send an MMS message with media attachments (images, videos, PDFs) using Twilio. Use this when you need to send visual content along with or instead of text.",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient phone number in E.164 format"
                    },
                    "from_": {
                        "type": "string",
                        "description": "Sender phone number (must be a Twilio phone number you own)"
                    },
                    "body": {
                        "type": "string",
                        "description": "Optional message text to accompany the media"
                    },
                    "media_url": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of media URLs to attach (max 10 attachments)"
                    },
                    "status_callback": {
                        "type": "string",
                        "description": "Optional webhook URL to receive delivery status updates"
                    }
                },
                "required": ["to", "from_"]
            },
            annotations=types.ToolAnnotations(**{"category": "TWILIO_MESSAGING"}),
        ),
        types.Tool(
            name="twilio_get_messages",
            description="Retrieve a list of SMS/MMS messages from your Twilio account. Use this to check message history, delivery status, or find specific conversations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of messages to retrieve (default 20, max 1000)",
                        "default": 20
                    },
                    "date_sent_after": {
                        "type": "string",
                        "description": "ISO date string to filter messages sent after this date (e.g., '2024-01-01')"
                    },
                    "date_sent_before": {
                        "type": "string", 
                        "description": "ISO date string to filter messages sent before this date"
                    },
                    "from_": {
                        "type": "string",
                        "description": "Filter by sender phone number"
                    },
                    "to": {
                        "type": "string",
                        "description": "Filter by recipient phone number"
                    }
                },
                "required": []
            },
            annotations=types.ToolAnnotations(**{"category": "TWILIO_MESSAGING", "readOnlyHint": True}),
        ),
        types.Tool(
            name="twilio_get_message_by_sid",
            description="Retrieve detailed information about a specific message using its unique SID. Use this when you need complete details about a particular message including delivery status and error information.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_sid": {
                        "type": "string",
                        "description": "Unique identifier (SID) for the message"
                    }
                },
                "required": ["message_sid"]
            },
            annotations=types.ToolAnnotations(**{"category": "TWILIO_MESSAGING", "readOnlyHint": True}),
        ),

        # Voice Call Tools
        types.Tool(
            name="twilio_make_call",
            description="Initiate a phone call using Twilio. You must provide either a TwiML URL or TwiML instructions to control what happens during the call (e.g., play message, collect input, record).",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Phone number to call in E.164 format"
                    },
                    "from_": {
                        "type": "string",
                        "description": "Caller phone number (must be a Twilio phone number you own)"
                    },
                    "url": {
                        "type": "string",
                        "description": "URL that returns TwiML instructions for the call"
                    },
                    "twiml": {
                        "type": "string",
                        "description": "TwiML instructions as a string (alternative to url)"
                    },
                    "method": {
                        "type": "string",
                        "description": "HTTP method for the webhook (GET or POST, default POST)"
                    },
                    "status_callback": {
                        "type": "string",
                        "description": "URL to receive call status updates"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Seconds to wait for an answer (default 60)"
                    },
                    "record": {
                        "type": "boolean",
                        "description": "Whether to record the call (default false)"
                    }
                },
                "required": ["to", "from_"]
            }
        ),
        types.Tool(
            name="twilio_get_calls",
            description="Retrieve a list of calls from your Twilio account. Use this to check call history, find calls with specific status, or analyze call patterns.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of calls to retrieve (default 20, max 1000)"
                    },
                    "status": {
                        "type": "string",
                        "description": "Filter by call status",
                        "enum": ["queued", "ringing", "in-progress", "completed", "busy", "failed", "no-answer", "canceled"]
                    },
                    "from_": {
                        "type": "string",
                        "description": "Filter by caller phone number"
                    },
                    "to": {
                        "type": "string",
                        "description": "Filter by called phone number"
                    },
                    "start_time_after": {
                        "type": "string",
                        "description": "ISO date string to filter calls started after this time"
                    },
                    "start_time_before": {
                        "type": "string",
                        "description": "ISO date string to filter calls started before this time"
                    }
                },
                "required": []
            },
            annotations=types.ToolAnnotations(**{"category": "TWILIO_VOICE", "readOnlyHint": True}),
        ),
        types.Tool(
            name="twilio_get_call_by_sid",
            description="Retrieve detailed information about a specific call using its unique SID. Use this to get complete call details including duration, status, and billing information.",
            inputSchema={
                "type": "object",
                "properties": {
                    "call_sid": {
                        "type": "string",
                        "description": "Unique identifier (SID) for the call"
                    }
                },
                "required": ["call_sid"]
            },
            annotations=types.ToolAnnotations(**{"category": "TWILIO_VOICE", "readOnlyHint": True}),
        ),
        types.Tool(
            name="twilio_get_recordings",
            description="Retrieve call recordings from your Twilio account. Use this to access recorded conversations for quality assurance, compliance, or analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of recordings to retrieve (default 20, max 1000)"
                    },
                    "call_sid": {
                        "type": "string",
                        "description": "Filter recordings by specific call SID"
                    },
                    "date_created_after": {
                        "type": "string",
                        "description": "ISO date string to filter recordings created after this date"
                    },
                    "date_created_before": {
                        "type": "string",
                        "description": "ISO date string to filter recordings created before this date"
                    }
                },
                "required": []
            },
            annotations=types.ToolAnnotations(**{"category": "TWILIO_VOICE", "readOnlyHint": True}),
        ),

        # Phone Number Management Tools
        types.Tool(
            name="twilio_search_available_numbers",
            description="Search for available phone numbers to purchase from Twilio. Use this to find numbers with specific area codes, capabilities (SMS/voice), or number patterns.",
            inputSchema={
                "type": "object",
                "properties": {
                    "country_code": {
                        "type": "string",
                        "description": "Two-letter country code (default 'US')",
                        "default": "US"
                    },
                    "area_code": {
                        "type": "string",
                        "description": "Specific area code to search within (e.g., '415' for San Francisco)"
                    },
                    "contains": {
                        "type": "string",
                        "description": "Search for numbers containing specific digits"
                    },
                    "sms_enabled": {
                        "type": "boolean",
                        "description": "Filter for SMS-capable numbers (default true)"
                    },
                    "voice_enabled": {
                        "type": "boolean",
                        "description": "Filter for voice-capable numbers (default true)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default 20, max 50)"
                    }
                },
                "required": []
            },
            annotations=types.ToolAnnotations(**{"category": "TWILIO_PHONE", "readOnlyHint": True}),
        ),
        types.Tool(
            name="twilio_purchase_phone_number",
            description="Purchase an available phone number from Twilio. Use this after finding a suitable number with search_available_numbers. You can configure webhooks for incoming calls and messages.",
            inputSchema={
                "type": "object",
                "properties": {
                    "phone_number": {
                        "type": "string",
                        "description": "Phone number to purchase in E.164 format"
                    },
                    "friendly_name": {
                        "type": "string",
                        "description": "A human-readable name for the number"
                    },
                    "voice_url": {
                        "type": "string",
                        "description": "URL to handle incoming voice calls"
                    },
                    "sms_url": {
                        "type": "string",
                        "description": "URL to handle incoming SMS messages"
                    },
                    "status_callback": {
                        "type": "string",
                        "description": "URL to receive status updates"
                    }
                },
                "required": ["phone_number"]
            },
            annotations=types.ToolAnnotations(**{"category": "TWILIO_PHONE"}),
        ),
        types.Tool(
            name="twilio_list_phone_numbers",
            description="List all phone numbers currently owned by your Twilio account. Use this to see your phone number inventory and their current configurations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of numbers to retrieve (default 20, max 1000)"
                    }
                },
                "required": []
            },
            annotations=types.ToolAnnotations(**{"category": "TWILIO_PHONE", "readOnlyHint": True}),
        ),
        types.Tool(
            name="twilio_update_phone_number",
            description="Update the configuration of an existing phone number. Use this to change webhook URLs, friendly names, or other settings for numbers you own.",
            inputSchema={
                "type": "object",
                "properties": {
                    "phone_number_sid": {
                        "type": "string",
                        "description": "SID of the phone number to update"
                    },
                    "friendly_name": {
                        "type": "string",
                        "description": "New friendly name for the number"
                    },
                    "voice_url": {
                        "type": "string",
                        "description": "New URL to handle incoming voice calls"
                    },
                    "sms_url": {
                        "type": "string",
                        "description": "New URL to handle incoming SMS messages"
                    },
                    "status_callback": {
                        "type": "string",
                        "description": "New URL to receive status updates"
                    }
                },
                "required": ["phone_number_sid"]
            },
            annotations=types.ToolAnnotations(**{"category": "TWILIO_PHONE"}),
        ),
        types.Tool(
            name="twilio_release_phone_number",
            description="Release (delete) a phone number from your Twilio account. This permanently removes the number and stops all billing for it. Use with caution as this action cannot be undone.",
            inputSchema={
                "type": "object",
                "properties": {
                    "phone_number_sid": {
                        "type": "string",
                        "description": "SID of the phone number to release"
                    }
                },
                "required": ["phone_number_sid"]
            },
            annotations=types.ToolAnnotations(**{"category": "TWILIO_PHONE"}),
        ),

        # Account & Usage Tools
        types.Tool(
            name="twilio_get_account_info",
            description="Retrieve your Twilio account information including status, type, and creation date. Use this to verify account details and current status.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            },
            annotations=types.ToolAnnotations(**{"category": "TWILIO_ACCOUNT", "readOnlyHint": True}),
        ),
        types.Tool(
            name="twilio_get_balance",
            description="Get the current balance of your Twilio account. Use this to check available credit and monitor spending.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            },
            annotations=types.ToolAnnotations(**{"category": "TWILIO_ACCOUNT", "readOnlyHint": True}),
        ),
        types.Tool(
            name="twilio_get_usage_records",
            description="Retrieve usage records for your Twilio account to analyze spending patterns, track usage by category, and generate usage reports. Perfect for billing analysis and cost monitoring.",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Usage category to filter by (e.g., 'sms', 'calls', 'recordings')"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date for usage period in YYYY-MM-DD format"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date for usage period in YYYY-MM-DD format"
                    },
                    "granularity": {
                        "type": "string",
                        "description": "Time granularity for the report",
                        "enum": ["daily", "monthly", "yearly", "all-time"],
                        "default": "daily"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of records to retrieve (default 50, max 1000)"
                    }
                },
                "required": []
            },
            annotations=types.ToolAnnotations(**{"category": "TWILIO_USAGE", "readOnlyHint": True}),
        ),
    ]

async def call_tool_router(name: str, arguments: dict) -> dict:
    """Unified tool router to avoid duplication between stdio and HTTP modes."""
    # Set auth token context from environment
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    if auth_token:
        auth_token_context.set(auth_token)
    
    logger.info(f"Calling tool: {name} with arguments: {arguments}")
    
    # Route to appropriate tool function
    if name == "twilio_send_sms":
        return await twilio_send_sms(**arguments)
    elif name == "twilio_send_mms":
        return await twilio_send_mms(**arguments)
    elif name == "twilio_get_messages":
        return await twilio_get_messages(**arguments)
    elif name == "twilio_get_message_by_sid":
        return await twilio_get_message_by_sid(**arguments)
    elif name == "twilio_make_call":
        return await twilio_make_call(**arguments)
    elif name == "twilio_get_calls":
        return await twilio_get_calls(**arguments)
    elif name == "twilio_get_call_by_sid":
        return await twilio_get_call_by_sid(**arguments)
    elif name == "twilio_get_recordings":
        return await twilio_get_recordings(**arguments)
    elif name == "twilio_search_available_numbers":
        return await twilio_search_available_numbers(**arguments)
    elif name == "twilio_purchase_phone_number":
        return await twilio_purchase_phone_number(**arguments)
    elif name == "twilio_list_phone_numbers":
        return await twilio_list_phone_numbers(**arguments)
    elif name == "twilio_update_phone_number":
        return await twilio_update_phone_number(**arguments)
    elif name == "twilio_release_phone_number":
        return await twilio_release_phone_number(**arguments)
    elif name == "twilio_get_account_info":
        return await twilio_get_account_info(**arguments)
    elif name == "twilio_get_balance":
        return await twilio_get_balance(**arguments)
    elif name == "twilio_get_usage_records":
        return await twilio_get_usage_records(**arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")

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
@click.option(
    "--stdio",
    is_flag=True,
    default=False,
    help="Run in stdio mode for Claude Desktop (instead of HTTP server mode)",
)
def main(
    port: int,
    log_level: str,
    json_response: bool,
    stdio: bool,
) -> int:
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    if stdio:
        # Run stdio mode for Claude Desktop
        return run_stdio_mode()
    else:
        # Run HTTP mode (default)
        return run_http_mode(port, json_response)


def run_stdio_mode() -> int:
    """Run the MCP server in stdio mode for Claude Desktop integration."""
    import sys
    
    def debug_log(message: str):
        print(f"[TWILIO-DEBUG] {message}", file=sys.stderr)
        sys.stderr.flush()

    debug_log("Twilio MCP Server initializing in stdio mode...")

    # Create the MCP server instance
    app = Server("twilio-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        debug_log("Listing tools requested")
        # Return all tools using shared function
        return get_all_tools()

    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        debug_log(f"Tool call requested: {name}")
        try:
            # Use shared tool router with auth context handling
            result = await call_tool_router(name, arguments)
            debug_log(f"Tool {name} completed successfully")
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            debug_log(f"Tool {name} failed: {str(e)}")
            logger.error(f"Error calling tool {name}: {e}")
            error_response = {
                "error": str(e),
                "tool": name,
                "arguments": arguments
            }
            return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
    
    async def run_server():
        debug_log("Starting stdio server...")
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
    
    asyncio.run(run_server())
    return 0


def run_http_mode(port: int, json_response: bool) -> int:
    """Run the MCP server in HTTP mode with dual transports."""
    
    # Create the MCP server instance
    app = Server("twilio-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        # Return all tools using shared function
        return get_all_tools()

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        try:
            # Use shared tool router with auth context handling
            result = await call_tool_router(name, arguments)
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

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        
        # Extract auth token from headers or use environment
        auth_token = request.headers.get('x-auth-token') or os.getenv("TWILIO_AUTH_TOKEN")
        
        # Set the auth token in context for this request
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
        stateless=True,
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        logger.info("Handling StreamableHTTP request")
        
        # Extract auth token from headers or use environment
        headers = dict(scope.get("headers", []))
        auth_token = headers.get(b'x-auth-token')
        if auth_token:
            auth_token = auth_token.decode('utf-8')
        else:
            auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        
        # Set the auth token in context for this request
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

    import uvicorn

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)

    return 0


if __name__ == "__main__":
    main()