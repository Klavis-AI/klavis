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

from tools import (
    zoom_access_token_context,
    zoom_create_meeting,
    zoom_get_meeting,
    zoom_update_meeting,
    zoom_delete_meeting,
    zoom_list_meetings,
    zoom_get_meeting_participants,
    zoom_create_webinar,
    zoom_get_user,
    zoom_list_users,
    validate_access_token,
)

logger = logging.getLogger("zoom-mcp-server")
logging.basicConfig(level=logging.INFO)

ZOOM_MCP_SERVER_PORT = int(os.getenv("ZOOM_MCP_SERVER_PORT", "5000"))


@click.command()
@click.option("--port", default=ZOOM_MCP_SERVER_PORT, help="Port to listen on for HTTP")
@click.option("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
@click.option("--json-response", is_flag=True, default=True, help="Enable JSON responses for StreamableHTTP")
def main(port: int, log_level: str, json_response: bool) -> int:
    """Zoom MCP server with SSE + StreamableHTTP transports using OAuth access tokens."""
    logging.getLogger().setLevel(getattr(logging, log_level.upper(), logging.INFO))
    app = Server("zoom-mcp-server")

    # ----------------------------- Tool Registry -----------------------------#
    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="zoom_create_meeting",
                description=(
                    "Create a new Zoom meeting with customizable settings like topic, time, duration, "
                    "and video/audio preferences.\n"
                    "Prompt hints: 'schedule a meeting', 'create zoom call', 'set up team standup'"
                ),
                inputSchema={
                    "type": "object",
                    "required": ["topic"],
                    "properties": {
                        "user_id": {"type": "string", "description": "User ID or 'me' for current user", "default": "me"},
                        "topic": {"type": "string", "description": "Meeting topic/title"},
                        "type": {"type": "integer", "description": "Meeting type: 1=instant, 2=scheduled, 3=recurring", "default": 2},
                        "start_time": {"type": "string", "description": "Start time in ISO format (YYYY-MM-DDTHH:MM:SSZ)"},
                        "duration": {"type": "integer", "description": "Meeting duration in minutes", "default": 60},
                        "timezone": {"type": "string", "description": "Timezone (e.g., 'America/New_York')", "default": "UTC"},
                        "password": {"type": "string", "description": "Meeting password"},
                        "host_video": {"type": "boolean", "description": "Host video on/off", "default": True},
                        "participant_video": {"type": "boolean", "description": "Participant video on/off", "default": True},
                        "join_before_host": {"type": "boolean", "description": "Allow joining before host", "default": False},
                        "mute_upon_entry": {"type": "boolean", "description": "Mute participants on entry", "default": False},
                        "watermark": {"type": "boolean", "description": "Add watermark", "default": False},
                        "use_pmi": {"type": "boolean", "description": "Use Personal Meeting ID", "default": False},
                        "approval_type": {"type": "integer", "description": "Approval type: 0=automatically, 1=manually, 2=no registration", "default": 0},
                        "audio": {"type": "string", "description": "Audio options: 'both', 'telephony', 'computer_audio'", "default": "both"},
                        "auto_recording": {"type": "string", "description": "Auto recording: 'none', 'local', 'cloud'", "default": "none"}
                    }
                }
            ),
            types.Tool(
                name="zoom_get_meeting",
                description=(
                    "Retrieve detailed information about a specific Zoom meeting including settings, "
                    "participants, and meeting status.\n"
                    "Prompt hints: 'get meeting details', 'show meeting info', 'check meeting settings'"
                ),
                inputSchema={
                    "type": "object",
                    "required": ["meeting_id"],
                    "properties": {
                        "meeting_id": {"type": "string", "description": "Zoom meeting ID"}
                    }
                }
            ),
            types.Tool(
                name="zoom_update_meeting",
                description=(
                    "Update meeting details like topic, time, duration, and settings for an existing Zoom meeting.\n"
                    "Prompt hints: 'change meeting time', 'update meeting topic', 'modify meeting settings'"
                ),
                inputSchema={
                    "type": "object",
                    "required": ["meeting_id"],
                    "properties": {
                        "meeting_id": {"type": "string", "description": "Zoom meeting ID"},
                        "topic": {"type": "string", "description": "New meeting topic/title"},
                        "type": {"type": "integer", "description": "Meeting type: 1=instant, 2=scheduled, 3=recurring"},
                        "start_time": {"type": "string", "description": "New start time in ISO format"},
                        "duration": {"type": "integer", "description": "New meeting duration in minutes"},
                        "timezone": {"type": "string", "description": "New timezone"},
                        "password": {"type": "string", "description": "New meeting password"},
                        "settings": {"type": "object", "description": "Meeting settings to update"}
                    }
                }
            ),
            types.Tool(
                name="zoom_delete_meeting",
                description=(
                    "Delete a Zoom meeting permanently. This action cannot be undone.\n"
                    "Prompt hints: 'cancel meeting', 'delete zoom call', 'remove meeting'"
                ),
                inputSchema={
                    "type": "object",
                    "required": ["meeting_id"],
                    "properties": {
                        "meeting_id": {"type": "string", "description": "Zoom meeting ID to delete"}
                    }
                }
            ),
            types.Tool(
                name="zoom_list_meetings",
                description=(
                    "List all meetings for a specific user with pagination support and filtering options.\n"
                    "Prompt hints: 'show my meetings', 'list all meetings', 'get meeting history'"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User ID or 'me' for current user", "default": "me"},
                        "type": {"type": "string", "description": "Meeting type filter: 'scheduled', 'live', 'upcoming'"},
                        "page_size": {"type": "integer", "description": "Number of meetings per page", "default": 30},
                        "page_number": {"type": "integer", "description": "Page number for pagination", "default": 1},
                        "next_page_token": {"type": "string", "description": "Token for next page"}
                    }
                }
            ),
            types.Tool(
                name="zoom_get_meeting_participants",
                description=(
                    "Get the list of participants for a specific meeting including join/leave times and duration.\n"
                    "Prompt hints: 'who joined the meeting', 'get participant list', 'show meeting attendees'"
                ),
                inputSchema={
                    "type": "object",
                    "required": ["meeting_id"],
                    "properties": {
                        "meeting_id": {"type": "string", "description": "Zoom meeting ID"}
                    }
                }
            ),
            types.Tool(
                name="zoom_create_webinar",
                description=(
                    "Create a new Zoom webinar with advanced settings for large audience events.\n"
                    "Prompt hints: 'create webinar', 'schedule online event', 'set up large meeting'"
                ),
                inputSchema={
                    "type": "object",
                    "required": ["topic"],
                    "properties": {
                        "user_id": {"type": "string", "description": "User ID or 'me' for current user", "default": "me"},
                        "topic": {"type": "string", "description": "Webinar topic/title"},
                        "type": {"type": "integer", "description": "Webinar type: 5=scheduled, 6=recurring, 9=recurring with fixed time", "default": 5},
                        "start_time": {"type": "string", "description": "Start time in ISO format"},
                        "duration": {"type": "integer", "description": "Webinar duration in minutes", "default": 60},
                        "timezone": {"type": "string", "description": "Timezone", "default": "UTC"},
                        "password": {"type": "string", "description": "Webinar password"},
                        "host_video": {"type": "boolean", "description": "Host video on/off", "default": True},
                        "panelists_video": {"type": "boolean", "description": "Panelists video on/off", "default": True},
                        "practice_session": {"type": "boolean", "description": "Enable practice session", "default": False},
                        "hd_video": {"type": "boolean", "description": "HD video quality", "default": True},
                        "audio": {"type": "string", "description": "Audio options", "default": "both"},
                        "auto_recording": {"type": "string", "description": "Auto recording", "default": "none"},
                        "alternative_hosts": {"type": "string", "description": "Alternative host email addresses"},
                        "close_registration": {"type": "boolean", "description": "Close registration", "default": False},
                        "show_share_button": {"type": "boolean", "description": "Show share button", "default": True},
                        "allow_multiple_devices": {"type": "boolean", "description": "Allow multiple devices", "default": False},
                        "on_demand": {"type": "boolean", "description": "On-demand webinar", "default": False},
                        "global_dial_in_countries": {"type": "array", "description": "Countries for dial-in"},
                        "contact_name": {"type": "string", "description": "Contact person name"},
                        "contact_email": {"type": "string", "description": "Contact person email"},
                        "registrants_restrict_number": {"type": "boolean", "description": "Restrict registrants", "default": False},
                        "registrants_email_notification": {"type": "boolean", "description": "Email notifications", "default": True}
                    }
                }
            ),
            types.Tool(
                name="zoom_get_user",
                description=(
                    "Get detailed information about a specific Zoom user including account type, "
                    "settings, and permissions.\n"
                    "Prompt hints: 'get user info', 'show user details', 'check user account'"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User ID or 'me' for current user", "default": "me"}
                    }
                }
            ),
            types.Tool(
                name="zoom_list_users",
                description=(
                    "List all users in the Zoom account with pagination and filtering options.\n"
                    "Prompt hints: 'show all users', 'list team members', 'get user directory'"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "description": "User status filter: 'active', 'inactive', 'pending'"},
                        "role_id": {"type": "string", "description": "Role ID filter"},
                        "page_size": {"type": "integer", "description": "Number of users per page", "default": 30},
                        "page_number": {"type": "integer", "description": "Page number for pagination", "default": 1},
                        "next_page_token": {"type": "string", "description": "Token for next page"}
                    }
                }
            ),
        ]

    # ---------------------------- Tool Dispatcher ----------------------------#
    @app.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> list[types.TextContent]:
        logger.info(f"call_tool: {name}")
        logger.debug(f"raw arguments: {json.dumps(arguments, indent=2)}")

        try:
            if name == "zoom_create_meeting":
                result = await zoom_create_meeting(arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

            if name == "zoom_get_meeting":
                result = await zoom_get_meeting(arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

            if name == "zoom_update_meeting":
                result = await zoom_update_meeting(arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

            if name == "zoom_delete_meeting":
                result = await zoom_delete_meeting(arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

            if name == "zoom_list_meetings":
                result = await zoom_list_meetings(arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

            if name == "zoom_get_meeting_participants":
                result = await zoom_get_meeting_participants(arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

            if name == "zoom_create_webinar":
                result = await zoom_create_webinar(arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

            if name == "zoom_get_user":
                result = await zoom_get_user(arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

            if name == "zoom_list_users":
                result = await zoom_list_users(arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
        except Exception as e:
            logger.exception(f"Error executing tool {name}: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

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

    import uvicorn
    uvicorn.run(starlette_app, host="0.0.0.0", port=port)

    return 0


if __name__ == "__main__":
    exit(main())
