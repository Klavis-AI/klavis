import contextlib
import logging
import os
import json
import base64
from collections.abc import AsyncIterator
from typing import Any, Dict, List

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
    # base.py
    auth_token_context,

    # schedule.py
    cal_get_all_schedules,
    cal_create_a_schedule,
    cal_update_a_schedule,
    cal_get_default_schedule,
    cal_get_schedule,
    cal_delete_a_schedule
)



# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

CAL_COM_MCP_SERVER_PORT = int(os.getenv("CAL_COM_MCP_SERVER_PORT", "5000"))

def extract_api_key(request_or_scope) -> str:
    """Extract API key from headers or environment."""
    api_key = os.getenv("API_KEY")
    
    if not api_key:
        # Handle different input types (request object for SSE, scope dict for StreamableHTTP)
        if hasattr(request_or_scope, 'headers'):
            # SSE request object
            auth_data = request_or_scope.headers.get(b'x-auth-data')
            if auth_data and isinstance(auth_data, bytes):
                auth_data = base64.b64decode(auth_data).decode('utf-8')
        elif isinstance(request_or_scope, dict) and 'headers' in request_or_scope:
            # StreamableHTTP scope object
            headers = dict(request_or_scope.get("headers", []))
            auth_data = headers.get(b'x-auth-data')
            if auth_data:
                auth_data = base64.b64decode(auth_data).decode('utf-8')
        else:
            auth_data = None
        
        if auth_data:
            try:
                # Parse the JSON auth data to extract token
                auth_json = json.loads(auth_data)
                api_key = auth_json.get('token') or auth_json.get('api_key') or ''
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to parse auth data JSON: {e}")
                api_key = ""
    
    return api_key or ""

@click.command()
@click.option("--port", default=CAL_COM_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("cal-com-mcp-server")
#-------------------------------------------------------------------
    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            # Get all schedules
            types.Tool(
                name="cal_get_all_schedules",
                description="Retrieve all schedules from Cal.com API.",
                inputSchema={
                    "type": "object",
                    "properties": {},  # No parameters required
                    "required": []
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CAL_SCHEDULE", "readOnlyHint": True}
                ),
            ),

            # Create a schedule
            types.Tool(
                name="cal_create_a_schedule",
                description="Create a new schedule in Cal.com.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the new schedule"
                        },
                        "timeZone": {
                            "type": "string",
                            "description": "Time zone ID (e.g., 'America/New_York')"
                        },
                        "isDefault": {
                            "type": "boolean",
                            "description": "Whether this should be the default schedule"
                        },
                        "availability": {
                            "type": "array",
                            "description": "List of availability blocks",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "days": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Capitalized day names (e.g., ['Monday','Tuesday'])"
                                    },
                                    "startTime": {
                                        "type": "string",
                                        "description": "Start time in HH:mm format"
                                    },
                                    "endTime": {
                                        "type": "string",
                                        "description": "End time in HH:mm format"
                                    }
                                }
                            }
                        },
                        "overrides": {
                            "type": "array",
                            "description": "Date-specific overrides",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "date": {
                                        "type": "string",
                                        "description": "Date in YYYY-MM-DD format"
                                    },
                                    "startTime": {
                                        "type": "string",
                                        "description": "Start time in HH:mm format"
                                    },
                                    "endTime": {
                                        "type": "string",
                                        "description": "End time in HH:mm format"
                                    }
                                }
                            }
                        }
                    },
                    "required": ["name", "timeZone", "isDefault"]
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CAL_SCHEDULE"}
                ),
            ),

            types.Tool(
                name="cal_update_a_schedule",
                description="Update an existing schedule in Cal.com.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "schedule_id": {
                            "type": "integer",
                            "description": "ID of the schedule to update"
                        },
                        "name": {
                            "type": "string",
                            "description": "Updated schedule name"
                        },
                        "timeZone": {
                            "type": "string",
                            "description": "Updated time zone ID (e.g., 'America/New_York')"
                        },
                        "isDefault": {
                            "type": "boolean",
                            "description": "Whether to make this the default schedule"
                        },
                        "availability": {
                            "type": "array",
                            "description": "Updated availability blocks",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "days": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Capitalized day names (e.g., ['Monday','Tuesday'])"
                                    },
                                    "startTime": {
                                        "type": "string",
                                        "description": "Start time in HH:mm format (e.g., '09:00')"
                                    },
                                    "endTime": {
                                        "type": "string",
                                        "description": "End time in HH:mm format (e.g., '17:00')"
                                    }
                                }
                            }
                        },
                        "overrides": {
                            "type": "array",
                            "description": "Updated date overrides",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "date": {
                                        "type": "string",
                                        "description": "Date in YYYY-MM-DD format (e.g., '2023-12-31')"
                                    },
                                    "startTime": {
                                        "type": "string",
                                        "description": "Start time in HH:mm format (e.g., '10:00')"
                                    },
                                    "endTime": {
                                        "type": "string",
                                        "description": "End time in HH:mm format (e.g., '15:00')"
                                    }
                                }
                            }
                        }
                    },
                    "required": ["schedule_id"]
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CAL_SCHEDULE"}
                ),
            ),

            # Get default schedule
            types.Tool(
                name="cal_get_default_schedule",
                description="Get the default schedule from Cal.com.",
                inputSchema={
                    "type": "object",
                    "properties": {},  # No parameters
                    "required": []
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CAL_SCHEDULE", "readOnlyHint": True}
                ),
            ),

            # Get specific schedule
            types.Tool(
                name="cal_get_schedule",
                description="Get a specific schedule by its ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "schedule_id": {
                            "type": "integer",
                            "description": "ID of the schedule to retrieve"
                        }
                    },
                    "required": ["schedule_id"]
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CAL_SCHEDULE", "readOnlyHint": True}
                ),
            ),

            # Delete a schedule
            types.Tool(
                name="cal_delete_a_schedule",
                description="Delete a schedule by its ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "schedule_id": {
                            "type": "integer",
                            "description": "ID of the schedule to delete"
                        }
                    },
                    "required": ["schedule_id"]
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CAL_SCHEDULE"}
                ),
            )
        ]

    @app.call_tool()
    async def call_tool(
            name: str,
            arguments: dict
    ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:

        #Schedule.py------------------------------------------------------------------
        if name == "cal_get_all_schedules":
            try:
                result = await cal_get_all_schedules()
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error getting all schedules: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "cal_create_a_schedule":
            try:
                result = await cal_create_a_schedule(
                    name=arguments["name"],
                    timeZone=arguments["timeZone"],
                    isDefault=arguments["isDefault"],
                    availability=arguments.get("availability"),
                    overrides=arguments.get("overrides")
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error creating schedule: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "cal_update_a_schedule":
            try:
                result = await cal_update_a_schedule(
                    schedule_id=arguments["schedule_id"],
                    name=arguments.get("name"),
                    timeZone=arguments.get("timeZone"),
                    isDefault=arguments.get("isDefault"),
                    availability=arguments.get("availability"),
                    overrides=arguments.get("overrides")
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error updating schedule: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "cal_get_default_schedule":
            try:
                result = await cal_get_default_schedule()
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error getting default schedule: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "cal_get_schedule":
            try:
                result = await cal_get_schedule(
                    schedule_id=arguments["schedule_id"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error getting schedule: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "cal_delete_a_schedule":
            try:
                result = await cal_delete_a_schedule(
                    schedule_id=arguments["schedule_id"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error deleting schedule: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
    #-------------------------------------------------------------------------

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")

        # Extract API key from headers
        api_key = extract_api_key(request)

        # Set the API key in context for this request
        token = auth_token_context.set(api_key)
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

        # Extract API key from headers
        api_key = extract_api_key(scope)

        # Set the API key in context for this request
        token = auth_token_context.set(api_key)
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
