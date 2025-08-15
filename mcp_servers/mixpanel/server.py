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
    import_events,
    set_user_profile,
    get_user_profile,
    query_events,
    get_event_count,
    get_top_events,
    list_saved_funnels,
    get_todays_top_events,
    get_profile_event_activity,
    get_projects,
    get_project_info,
)

logger = logging.getLogger(__name__)

load_dotenv()

MIXPANEL_MCP_SERVER_PORT = int(os.getenv("MIXPANEL_MCP_SERVER_PORT", "5000"))

@click.command()
@click.option("--port", default=MIXPANEL_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("mixpanel-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="mixpanel_import_events",
                title="Import Events",
                description="Import events to Mixpanel using the /import endpoint with Service Account authentication. Send batches of events with automatic deduplication support. Each event requires time, distinct_id, and $insert_id for proper processing.",
                inputSchema={
                    "type": "object",
                    "required": ["project_id", "events"],
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "The Mixpanel project ID to import events to. Use get_projects tool to find available project IDs.",
                        },
                        "events": {
                            "type": "array",
                            "description": "Array of event objects to import",
                            "items": {
                                "type": "object",
                                "required": ["event"],
                                "properties": {
                                    "event": {
                                        "type": "string",
                                        "description": "The name of the event (e.g., 'Page View', 'Button Click', 'Purchase')",
                                    },
                                    "properties": {
                                        "type": "object",
                                        "description": "Event properties. Will auto-generate time and $insert_id if not provided.",
                                        "additionalProperties": True,
                                    },
                                    "distinct_id": {
                                        "type": "string",
                                        "description": "Unique identifier for the user performing the event (empty string if anonymous)",
                                    },
                                },
                            },
                            "minItems": 1,
                            "maxItems": 2000,
                        },
                    },
                },
            ),
            types.Tool(
                name="mixpanel_set_user_profile",
                title="Set User Profile",
                description="Set user profile properties in Mixpanel People. Create or update user profiles with demographic information, preferences, subscription details, and other user attributes for advanced segmentation and personalization.",
                inputSchema={
                    "type": "object",
                    "required": ["project_id", "distinct_id"],
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "The Mixpanel project ID. Use get_projects tool to find available project IDs.",
                        },
                        "distinct_id": {
                            "type": "string",
                            "description": "Unique identifier for the user (e.g., user ID, email address)",
                        },
                        "properties": {
                            "type": "object",
                            "description": "User profile properties to set (e.g., name, email, age, plan_type, signup_date)",
                            "additionalProperties": True,
                        },
                        "operation": {
                            "type": "string",
                            "enum": ["$set", "$set_once", "$add", "$append", "$union", "$remove", "$unset", "$delete"],
                            "default": "$set",
                            "description": "Mixpanel operation type: $set (update), $set_once (only if not exists), $add (increment), $append (add to list), $union (merge lists), $remove (remove from list), $unset (remove property), $delete (delete profile)",
                        },
                    },
                },
            ),
            types.Tool(
                name="mixpanel_get_user_profile",
                title="Get User Profile",
                description="Retrieve user profile data from Mixpanel People. Get demographic information, preferences, subscription details, and other user attributes for a specific user to analyze their profile and behavior patterns.",
                inputSchema={
                    "type": "object",
                    "required": ["distinct_id"],
                    "properties": {
                        "distinct_id": {
                            "type": "string",
                            "description": "Unique identifier for the user to retrieve (e.g., user ID, email address)",
                        },
                    },
                },
            ),
            types.Tool(
                name="mixpanel_query_events",
                title="Query Events",
                description="Query raw event data from Mixpanel. Retrieve historical events with optional filtering by event name, date range, and custom properties for detailed analysis and reporting.",
                inputSchema={
                    "type": "object",
                    "required": ["from_date", "to_date"],
                    "properties": {
                        "from_date": {
                            "type": "string",
                            "description": "Start date for query in YYYY-MM-DD format (e.g., '2024-01-01')",
                        },
                        "to_date": {
                            "type": "string", 
                            "description": "End date for query in YYYY-MM-DD format (e.g., '2024-01-31')",
                        },
                        "event": {
                            "type": "string",
                            "description": "Optional specific event name to filter results (e.g., 'Page View', 'Purchase')",
                        },
                        "where": {
                            "type": "string",
                            "description": "Optional JSON where clause for advanced filtering (e.g., '{\"properties\":{\"$browser\":\"Chrome\"}}')",
                        },
                        "limit": {
                            "type": "integer",
                            "default": 1000,
                            "description": "Maximum number of events to return (default: 1000, max: 10000)",
                        },
                    },
                },
            ),
            types.Tool(
                name="mixpanel_get_projects",
                title="Get Projects",
                description="Get all projects that are accessible to the current service account user. Use this tool to discover available projects and their IDs, which are required for event tracking and user profile operations.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="mixpanel_get_project_info",
                title="Get Project Info",
                description="Get detailed information about a specific project including workspaces and metadata. Useful when a user specifies a project ID to get more details about that project.",
                inputSchema={
                    "type": "object",
                    "required": ["project_id"],
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "The Mixpanel project ID to get information for",
                        },
                    },
                },
            ),
            types.Tool(
                name="mixpanel_get_event_count",
                title="Get Event Count",
                description="Get total event count for a specific date range from Mixpanel analytics. Provides comprehensive statistics including total events, unique users, and event breakdown by type for analysis and reporting.",
                inputSchema={
                    "type": "object",
                    "required": ["from_date", "to_date"],
                    "properties": {
                        "from_date": {
                            "type": "string",
                            "description": "Start date for count query in YYYY-MM-DD format (e.g., '2024-01-01')",
                        },
                        "to_date": {
                            "type": "string",
                            "description": "End date for count query in YYYY-MM-DD format (e.g., '2024-01-31')",
                        },
                        "event": {
                            "type": "string",
                            "description": "Optional specific event name to count (e.g., 'Page View', 'Purchase'). If not provided, counts all events.",
                        },
                    },
                },
            ),
            types.Tool(
                name="mixpanel_get_top_events",
                title="Get Top Events",
                description="Get a list of the most common events over a specified time period from Mixpanel analytics. Provides event rankings with counts and percentages for identifying popular user actions and behaviors.",
                inputSchema={
                    "type": "object",
                    "required": ["from_date", "to_date"],
                    "properties": {
                        "from_date": {
                            "type": "string",
                            "description": "Start date for analysis in YYYY-MM-DD format (e.g., '2024-01-01')",
                        },
                        "to_date": {
                            "type": "string",
                            "description": "End date for analysis in YYYY-MM-DD format (e.g., '2024-01-31')",
                        },
                        "limit": {
                            "type": "integer",
                            "default": 10,
                            "description": "Maximum number of top events to return (default: 10, max: 100)",
                        },
                    },
                },
            ),
            types.Tool(
                name="mixpanel_list_saved_funnels",
                title="List Saved Funnels",
                description="Get a list of all saved funnels from Mixpanel with their names, funnel IDs, and metadata. Retrieve funnel information including creation dates, creators, step counts, and descriptions for analysis and reporting.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="mixpanel_get_todays_top_events",
                title="Get Today's Top Events",
                description="Get the most common events from today's date from Mixpanel analytics. Provides real-time insights into current user activity and popular actions happening right now with event rankings and counts.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "default": 10,
                            "description": "Maximum number of top events to return (default: 10, max: 100)",
                        },
                    },
                },
            ),
            types.Tool(
                name="mixpanel_get_profile_event_activity",
                title="Get Profile Event Activity",
                description="Get event activity feed for a specific user from Mixpanel analytics. Retrieve chronological list of all events performed by a user with timestamps, properties, and activity summary for user behavior analysis.",
                inputSchema={
                    "type": "object",
                    "required": ["distinct_id"],
                    "properties": {
                        "distinct_id": {
                            "type": "string",
                            "description": "Unique identifier for the user (e.g., user ID, email address)",
                        },
                        "from_date": {
                            "type": "string",
                            "description": "Start date for activity search in YYYY-MM-DD format (e.g., '2024-01-01'). Defaults to 30 days ago if not provided.",
                        },
                        "to_date": {
                            "type": "string",
                            "description": "End date for activity search in YYYY-MM-DD format (e.g., '2024-01-31'). Defaults to today if not provided.",
                        },
                        "limit": {
                            "type": "integer",
                            "default": 100,
                            "description": "Maximum number of events to return (default: 100, max: 1000)",
                        },
                    },
                },
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        
        if name == "mixpanel_import_events":
            project_id = arguments.get("project_id")
            events = arguments.get("events")
            
            if not project_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: project_id parameter is required",
                    )
                ]
                
            if not events:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: events parameter is required",
                    )
                ]
            
            try:
                result = await import_events(project_id, events)
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
        
        elif name == "mixpanel_set_user_profile":
            project_id = arguments.get("project_id")
            distinct_id = arguments.get("distinct_id")
            
            if not project_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: project_id parameter is required",
                    )
                ]
                
            if not distinct_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: distinct_id parameter is required",
                    )
                ]
            
            properties = arguments.get("properties")
            operation = arguments.get("operation", "$set")
            
            try:
                result = await set_user_profile(project_id, distinct_id, properties, operation)
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
        
        elif name == "mixpanel_get_user_profile":
            distinct_id = arguments.get("distinct_id")
            if not distinct_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: distinct_id parameter is required",
                    )
                ]
            
            try:
                result = await get_user_profile(distinct_id)
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
        
        elif name == "mixpanel_query_events":
            from_date = arguments.get("from_date")
            to_date = arguments.get("to_date")
            
            if not from_date or not to_date:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: from_date and to_date parameters are required",
                    )
                ]
            
            event = arguments.get("event")
            where = arguments.get("where")
            limit = arguments.get("limit", 1000)
            
            try:
                result = await query_events(from_date, to_date, event, where, limit)
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
        
        elif name == "mixpanel_get_projects":
            try:
                result = await get_projects()
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
        
        elif name == "mixpanel_get_project_info":
            project_id = arguments.get("project_id")
            
            if not project_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: project_id parameter is required",
                    )
                ]
            
            try:
                result = await get_project_info(project_id)
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
        
        elif name == "mixpanel_get_event_count":
            from_date = arguments.get("from_date")
            to_date = arguments.get("to_date")
            
            if not from_date or not to_date:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: from_date and to_date parameters are required",
                    )
                ]
            
            event = arguments.get("event")
            
            try:
                result = await get_event_count(from_date, to_date, event)
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
        
        elif name == "mixpanel_get_top_events":
            from_date = arguments.get("from_date")
            to_date = arguments.get("to_date")
            
            if not from_date or not to_date:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: from_date and to_date parameters are required",
                    )
                ]
            
            limit = arguments.get("limit", 10)
            
            try:
                result = await get_top_events(from_date, to_date, limit)
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
        
        elif name == "mixpanel_list_saved_funnels":
            try:
                result = await list_saved_funnels()
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
        
        elif name == "mixpanel_get_todays_top_events":
            limit = arguments.get("limit", 10)
            
            try:
                result = await get_todays_top_events(limit)
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
        
        elif name == "mixpanel_get_profile_event_activity":
            distinct_id = arguments.get("distinct_id")
            if not distinct_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: distinct_id parameter is required",
                    )
                ]
            
            from_date = arguments.get("from_date")
            to_date = arguments.get("to_date")
            limit = arguments.get("limit", 100)
            
            try:
                result = await get_profile_event_activity(distinct_id, from_date, to_date, limit)
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
        event_store=None,
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        logger.info("Handling StreamableHTTP request")
        
        # Extract auth token from headers (allow None - will be handled at tool level)
        headers = dict(scope.get("headers", []))
        auth_token = headers.get(b'x-auth-token')
        if auth_token:
            auth_token = auth_token.decode('utf-8')
        
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

    import uvicorn

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)

    return 0

if __name__ == "__main__":
    main()