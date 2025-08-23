import os
import logging
import contextlib
import json
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional
from contextvars import ContextVar

import click
from dotenv import load_dotenv
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

from tools import (
    auth_token_context,
    get_user_info,
    list_events,
    get_event_details,
    list_event_types,
    list_availability_schedules,
    list_event_invitees,
)

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

CALENDLY_MCP_SERVER_PORT = int(os.getenv("CALENDLY_MCP_SERVER_PORT", "5000"))

@click.command()
@click.option("--port", default=CALENDLY_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("calendly-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="calendly_get_user_info",
                description="Get current user's Calendly profile information.",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            types.Tool(
                name="calendly_list_events",
                description="List scheduled events for the current user.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "Filter events by status (active, canceled). Leave empty for all.",
                            "enum": ["active", "canceled"]
                        },
                        "count": {
                            "type": "integer",
                            "description": "Number of events to return (max 100).",
                            "default": 20,
                            "maximum": 100
                        }
                    }
                }
            ),
            types.Tool(
                name="calendly_get_event_details",
                description="Get detailed information about a specific event.",
                inputSchema={
                    "type": "object",
                    "required": ["event_uuid"],
                    "properties": {
                        "event_uuid": {
                            "type": "string",
                            "description": "The UUID of the event to retrieve details for."
                        }
                    }
                }
            ),
            types.Tool(
                name="calendly_list_event_types",
                description="List available event types for the current user.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "active": {
                            "type": "boolean",
                            "description": "Filter by active status. Leave empty for all.",
                            "default": True
                        },
                        "count": {
                            "type": "integer",
                            "description": "Number of event types to return (max 100).",
                            "default": 20,
                            "maximum": 100
                        }
                    }
                }
            ),
            types.Tool(
                name="calendly_list_availability_schedules",
                description="List the availability schedules of the given user.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_uri": {
                            "type": "string",
                            "description": "The URI of the user to get availability schedules for. If not provided, uses current user."
                        },
                        "count": {
                            "type": "integer",
                            "description": "Number of availability schedules to return (max 100).",
                            "default": 20,
                            "maximum": 100
                        }
                    }
                }
            ),
            types.Tool(
                name="calendly_list_event_invitees",
                description="List invitees for a specific scheduled event.",
                inputSchema={
                    "type": "object",
                    "required": ["event_uuid"],
                    "properties": {
                        "event_uuid": {
                            "type": "string",
                            "description": "The UUID of the event to list invitees for."
                        },
                        "count": {
                            "type": "integer",
                            "description": "Number of invitees to return (max 100).",
                            "default": 20,
                            "maximum": 100
                        },
                        "email": {
                            "type": "string",
                            "description": "Filter invitees by email address."
                        },
                        "status": {
                            "type": "string",
                            "description": "Filter invitees by status.",
                            "enum": ["active", "canceled"]
                        }
                    }
                }
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        
        if name == "calendly_get_user_info":
            try:
                result = await get_user_info()
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
        
        elif name == "calendly_list_events":
            status = arguments.get("status")
            count = arguments.get("count", 20)
            try:
                result = await list_events(status, count)
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
        
        elif name == "calendly_get_event_details":
            event_uuid = arguments.get("event_uuid")
            if not event_uuid:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: event_uuid parameter is required",
                    )
                ]
            try:
                result = await get_event_details(event_uuid)
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
        
        elif name == "calendly_list_event_types":
            active = arguments.get("active", True)
            count = arguments.get("count", 20)
            try:
                result = await list_event_types(active, count)
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
        
        elif name == "calendly_list_availability_schedules":
            user_uri = arguments.get("user_uri")
            count = arguments.get("count", 20)
            try:
                result = await list_availability_schedules(user_uri, count)
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
        
        elif name == "calendly_list_event_invitees":
            event_uuid = arguments.get("event_uuid")
            count = arguments.get("count", 20)
            email = arguments.get("email")
            status = arguments.get("status")
            if not event_uuid:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: event_uuid parameter is required",
                    )
                ]
            try:
                result = await list_event_invitees(event_uuid, count, email, status)
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
            return [
                types.TextContent(
                    type="text",
                    text=f"Unknown tool: {name}",
                )
            ]

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        
        # Extract auth token from headers (allow None - will be handled at tool level)
        calendly_token = request.headers.get('x-auth-token')
        
        # Set the auth token in context for this request (can be None)
        token = auth_token_context.set(calendly_token or "")
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
        
        # Extract auth token from headers (allow None - will be handled at tool level)
        headers = dict(scope.get("headers", []))
        calendly_token = headers.get(b'x-auth-token')
        if calendly_token:
            calendly_token = calendly_token.decode('utf-8')
        
        # Set the auth token in context for this request (can be None/empty)
        token = auth_token_context.set(calendly_token or "")
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