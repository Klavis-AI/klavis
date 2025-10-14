import contextlib
import logging
import os
import json
from collections.abc import AsyncIterator
from typing import Any
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
from googleapiclient.errors import HttpError

try:  # Support running as module or script
    from .tools.utils import (
        ValidationError,
        validate_time_window,
        validate_attendees,
        parse_rfc3339,
        success,
        failure,
        shape_meeting,
        http_error_to_message,
    )
except ImportError:  # Fallback when executed directly
    from tools.utils import (
        ValidationError,
        validate_time_window,
        validate_attendees,
        parse_rfc3339,
        success,
        failure,
        shape_meeting,
        http_error_to_message,
    )

logger = logging.getLogger(__name__)
load_dotenv()
GOOGLE_MEET_MCP_SERVER_PORT = int(os.getenv("GOOGLE_MEET_MCP_SERVER_PORT", "5000"))

# Import core logic from tools.base
try:
    from .tools.base import (
        auth_token_context,
        extract_access_token,
        get_auth_token,
        create_meet,
        list_meetings,
        list_past_meetings,
        get_meeting_details,
        update_meeting,
        delete_meeting,
        get_past_meeting_attendees,
    )
    from .tools import meet_api as meet_v2
except ImportError:
    from tools.base import (
        auth_token_context,
        extract_access_token,
        get_auth_token,
        create_meet,
        list_meetings,
        list_past_meetings,
        get_meeting_details,
        update_meeting,
        delete_meeting,
        get_past_meeting_attendees,
    )
    import tools.meet_api as meet_v2

## Core tool implementations now imported from tools.base

@click.command()
@click.option("--port", default=GOOGLE_MEET_MCP_SERVER_PORT, help="Port to listen on for HTTP")
@click.option("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
@click.option("--json-response", is_flag=True, default=False, help="Enable JSON responses for StreamableHTTP instead of SSE streams")
@click.option("--stdio", is_flag=True, default=False, help="Run with stdio transport instead of HTTP")
def main(port: int, log_level: str, json_response: bool, stdio: bool) -> int:
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    app = Server("google-meet-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        tools = [
            types.Tool(
                name="google_meet_create_meet",
                description="Create a new Google Meet meeting (via Calendar event)",
                inputSchema={
                    "type": "object",
                    "required": ["summary", "start_time", "end_time", "attendees"],
                    "properties": {
                        "summary": {"type": "string", "description": "Meeting title"},
                        "start_time": {"type": "string", "description": "ISO RFC3339 datetime"},
                        "end_time": {"type": "string", "description": "ISO RFC3339 datetime"},
                        "attendees": {"type": "array", "items": {"type": "string"}, "description": "List of attendee email addresses"},
                        "description": {"type": "string", "description": "Meeting description"},
                        "notify_attendees": {"type": "boolean", "description": "Send calendar invitations to attendees (default true)", "default": True},
                    },
                },
            ),
            types.Tool(
                name="google_meet_list_meetings",
                description="List upcoming Google Meet meetings from the user's calendar",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "max_results": {"type": "integer", "description": "Maximum number of meetings to return (1-100)", "default": 10},
                        "start_after": {"type": "string", "description": "Only meetings starting after this RFC3339 UTC time"},
                        "end_before": {"type": "string", "description": "Only meetings starting before this RFC3339 UTC time"},
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "GOOGLE_MEET_MEETING", "readOnlyHint": True}),
            ),
            types.Tool(
                name="google_meet_list_past_meetings",
                description="List past Google Meet meetings (already ended) in descending recency",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "max_results": {"type": "integer", "description": "Maximum number of past meetings to return (1-100)", "default": 10},
                        "since": {"type": "string", "description": "Only include meetings starting after this RFC3339 UTC time"},
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "GOOGLE_MEET_MEETING", "readOnlyHint": True}),
            ),
            types.Tool(
                name="google_meet_get_meeting_details",
                description="Get details of a specific Google Meet meeting",
                inputSchema={
                    "type": "object",
                    "required": ["event_id"],
                    "properties": {
                        "event_id": {"type": "string", "description": "The calendar event ID of the meeting"},
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "GOOGLE_MEET_MEETING", "readOnlyHint": True}),
            ),
            types.Tool(
                name="google_meet_update_meeting",
                description="Update an existing Google Meet meeting",
                inputSchema={
                    "type": "object",
                    "required": ["event_id"],
                    "properties": {
                        "event_id": {"type": "string", "description": "The calendar event ID of the meeting"},
                        "summary": {"type": "string", "description": "New meeting title"},
                        "start_time": {"type": "string", "description": "New start time (ISO RFC3339)"},
                        "end_time": {"type": "string", "description": "New end time (ISO RFC3339)"},
                        "attendees": {"type": "array", "items": {"type": "string"}, "description": "New list of attendee email addresses"},
                        "description": {"type": "string", "description": "New meeting description"},
                        "notify_attendees": {"type": "boolean", "description": "Send updated invitations / notifications (default true)", "default": True},
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "GOOGLE_MEET_MEETING"}),
            ),
            types.Tool(
                name="google_meet_delete_meeting",
                description="Delete a Google Meet meeting",
                inputSchema={
                    "type": "object",
                    "required": ["event_id"],
                    "properties": {
                        "event_id": {"type": "string", "description": "The calendar event ID of the meeting to delete"},
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "GOOGLE_MEET_MEETING"}),
            ),
            types.Tool(
                name="google_meet_get_past_meeting_attendees",
                description="Get attendees (with response statuses) for a past meeting (fails if meeting not ended)",
                inputSchema={
                    "type": "object",
                    "required": ["event_id"],
                    "properties": {
                        "event_id": {"type": "string", "description": "The calendar event ID of the past meeting"},
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "GOOGLE_MEET_MEETING", "readOnlyHint": True}),
            ),
        ]
        tools.extend([
            types.Tool(
                name="google_meet_v2_create_instant",
                description="Create an instant ad-hoc Google Meet (Meet API v2, Workspace/EDU only)",
                inputSchema={"type": "object", "properties": {}},
                annotations=types.ToolAnnotations(**{"category": "GOOGLE_MEET_V2"}),
            ),
            types.Tool(
                name="google_meet_v2_get_meeting",
                description="Get Meet API v2 meeting (space) details (Workspace/EDU)",
                inputSchema={
                    "type": "object",
                    "required": ["space_id"],
                    "properties": {"space_id": {"type": "string", "description": "Space ID or spaces/<id>"}},
                },
                annotations=types.ToolAnnotations(**{"category": "GOOGLE_MEET_V2", "readOnlyHint": True}),
            ),
            types.Tool(
                name="google_meet_v2_list_meetings",
                description="List Meet API v2 meetings/spaces (Workspace/EDU)",
                inputSchema={
                    "type": "object",
                    "properties": {"max_results": {"type": "integer", "default": 10, "description": "1-100"}},
                },
                annotations=types.ToolAnnotations(**{"category": "GOOGLE_MEET_V2", "readOnlyHint": True}),
            ),
            types.Tool(
                name="google_meet_v2_get_participants",
                description="Get participants for a Meet API v2 meeting (Workspace/EDU)",
                inputSchema={
                    "type": "object",
                    "required": ["space_id"],
                    "properties": {
                        "space_id": {"type": "string", "description": "Space ID or spaces/<id>"},
                        "max_results": {"type": "integer", "default": 50, "description": "1-300"},
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "GOOGLE_MEET_V2", "readOnlyHint": True}),
            ),
        ])
        return tools
    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        if name == "google_meet_create_meet":
            summary = arguments.get("summary")
            start_time = arguments.get("start_time")
            end_time = arguments.get("end_time")
            attendees = arguments.get("attendees", [])
            description = arguments.get("description", "")
            notify_attendees = arguments.get("notify_attendees", True)
            result = await create_meet(summary, start_time, end_time, attendees, description, notify_attendees)
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "google_meet_list_meetings":
            max_results = arguments.get("max_results", 10)
            start_after = arguments.get("start_after")
            end_before = arguments.get("end_before")
            result = await list_meetings(max_results, start_after, end_before)
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "google_meet_list_past_meetings":
            max_results = arguments.get("max_results", 10)
            since = arguments.get("since")
            result = await list_past_meetings(max_results, since)
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "google_meet_get_meeting_details":
            event_id = arguments.get("event_id")
            if not event_id:
                return [types.TextContent(type="text", text=json.dumps(failure("event_id parameter is required")))]
            result = await get_meeting_details(event_id)
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "google_meet_update_meeting":
            event_id = arguments.get("event_id")
            if not event_id:
                return [types.TextContent(type="text", text=json.dumps(failure("event_id parameter is required")))]
            summary = arguments.get("summary")
            start_time = arguments.get("start_time")
            end_time = arguments.get("end_time")
            attendees = arguments.get("attendees")
            description = arguments.get("description")
            notify_attendees = arguments.get("notify_attendees", True)
            result = await update_meeting(event_id, summary, start_time, end_time, attendees, description, notify_attendees)
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "google_meet_delete_meeting":
            event_id = arguments.get("event_id")
            if not event_id:
                return [types.TextContent(type="text", text=json.dumps(failure("event_id parameter is required")))]
            result = await delete_meeting(event_id)
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "google_meet_get_past_meeting_attendees":
            event_id = arguments.get("event_id")
            if not event_id:
                return [types.TextContent(type="text", text=json.dumps(failure("event_id parameter is required")))]
            result = await get_past_meeting_attendees(event_id)
            return [types.TextContent(type="text", text=json.dumps(result))]
        # ----------------Meet API v2 tools-----------------
        elif name == "google_meet_v2_create_instant":
            try:
                result = await meet_v2.create_instant_meeting()
            except Exception as e:  # Safety net
                logger.exception("meet_v2_create_instant unexpected error=%s", e)
                result = failure("Unexpected server error", code="internal_error")
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "google_meet_v2_get_meeting":
            space_id = arguments.get("space_id")
            if not space_id:
                return [types.TextContent(type="text", text=json.dumps(failure("space_id parameter is required")))]
            try:
                result = await meet_v2.get_meeting(space_id)
            except Exception as e:
                logger.exception("meet_v2_get_meeting unexpected error=%s", e)
                result = failure("Unexpected server error", code="internal_error")
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "google_meet_v2_list_meetings":
            max_results = arguments.get("max_results", 10)
            try:
                result = await meet_v2.list_meetings(max_results)
            except Exception as e:
                logger.exception("meet_v2_list_meetings unexpected error=%s", e)
                result = failure("Unexpected server error", code="internal_error")
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "google_meet_v2_get_participants":
            space_id = arguments.get("space_id")
            if not space_id:
                return [types.TextContent(type="text", text=json.dumps(failure("space_id parameter is required")))]
            max_results = arguments.get("max_results", 50)
            try:
                result = await meet_v2.get_participants(space_id, max_results)
            except Exception as e:
                logger.exception("meet_v2_get_participants unexpected error=%s", e)
                result = failure("Unexpected server error", code="internal_error")
            return [types.TextContent(type="text", text=json.dumps(result))]
        return [types.TextContent(type="text", text=json.dumps(failure(f"Unknown tool: {name}", code="unknown_tool")))]
    
    if stdio:
        logger.info("Starting Google Meet MCP server with stdio transport")
        import asyncio
        async def run_stdio():
            auth_token = extract_access_token(None)
            if not auth_token:
                logger.error("No access token found in AUTH_DATA environment variable")
                return
            
            token = auth_token_context.set(auth_token)
            try:
                async with stdio_server() as (read_stream, write_stream):
                    await app.run(read_stream, write_stream, app.create_initialization_options())
            finally:
                auth_token_context.reset(token)
        asyncio.run(run_stdio())
        return 0

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        
        auth_token = extract_access_token(request)
        
        token = auth_token_context.set(auth_token)
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
        
        auth_token = extract_access_token(scope)
        
        token = auth_token_context.set(auth_token)
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
