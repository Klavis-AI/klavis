import contextlib
import base64
import logging
import os
import json
import datetime
from collections.abc import AsyncIterator
from typing import Any, Dict, List
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
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
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
except ImportError:  # Fallback when executed directly (python server.py)
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

auth_token_context: ContextVar[str] = ContextVar('auth_token')

def extract_access_token(request_or_scope) -> str:
    auth_data = os.getenv("AUTH_DATA")
    if not auth_data:
        if hasattr(request_or_scope, 'headers'):
            auth_data = request_or_scope.headers.get(b'x-auth-data')
            if auth_data:
                auth_data = base64.b64decode(auth_data).decode('utf-8')
        elif isinstance(request_or_scope, dict) and 'headers' in request_or_scope:
            headers = dict(request_or_scope.get("headers", []))
            auth_data = headers.get(b'x-auth-data')
            if auth_data:
                auth_data = base64.b64decode(auth_data).decode('utf-8')
    if not auth_data:
        return ""
    try:
        auth_json = json.loads(auth_data)
        return auth_json.get('access_token', '')
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse auth data JSON: {e}")
        return ""

def get_calendar_service(access_token: str):
    credentials = Credentials(token=access_token)
    return build('calendar', 'v3', credentials=credentials)

def get_auth_token() -> str:
    try:
        return auth_token_context.get()
    except LookupError:
        # Return empty string so callers can return a clean failure() response
        return ""

async def create_meet(summary: str, start_time: str, end_time: str, attendees: List[str], description: str = "") -> Dict[str, Any]:
    logger.info(f"tool=create_meet action=start summary='{summary}'")
    try:
        if not summary or not start_time or not end_time or attendees is None:
            return failure("Missing required fields", details={"required": ["summary", "start_time", "end_time", "attendees"]})
        # Validation
        validate_time_window(start_time, end_time)
        validate_attendees(attendees)
        access_token = get_auth_token()
        if not access_token:
            return failure("Missing access token", code="unauthorized")
        service = get_calendar_service(access_token)
        event = {
            'summary': summary,
            'description': description or "",
            'start': {'dateTime': start_time, 'timeZone': 'UTC'},
            'end': {'dateTime': end_time, 'timeZone': 'UTC'},
            'attendees': [{'email': email} for email in attendees],
            'conferenceData': {
                'createRequest': {
                    'requestId': os.urandom(8).hex(),
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                }
            }
        }
        created_event = service.events().insert(
            calendarId='primary',
            body=event,
            conferenceDataVersion=1,
        ).execute()
        data = shape_meeting(created_event)
        logger.info(f"tool=create_meet action=success event_id={data.get('event_id')}")
        return success(data)
    except ValidationError as ve:
        logger.warning(f"tool=create_meet validation_error={ve}")
        return failure(str(ve))
    except HttpError as e:
        status = getattr(e.resp, 'status', 0)
        detail = http_error_to_message(status, "Google Calendar API error")
        try:
            error_detail = json.loads(e.content.decode('utf-8'))
        except Exception:
            error_detail = {}
        logger.error(f"tool=create_meet http_error status={status} msg={detail}")
        return failure(detail, code=str(status or 'http_error'), details=error_detail)
    except Exception as e:
        logger.exception(f"tool=create_meet unexpected_error={e}")
        return failure("Unexpected server error", code="internal_error")

async def list_meetings(max_results: int = 10, start_after: str | None = None, end_before: str | None = None) -> Dict[str, Any]:
    """List upcoming Google Meet meetings from the user's calendar.

    Optional filters: start_after (timeMin), end_before (timeMax)
    """
    logger.info(f"tool=list_meetings action=start max_results={max_results}")
    try:
        if max_results <= 0 or max_results > 100:
            return failure("max_results must be between 1 and 100")
        access_token = get_auth_token()
        if not access_token:
            return failure("Missing access token", code="unauthorized")
        service = get_calendar_service(access_token)
        now = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
        time_min = start_after or now
        if start_after:
            parse_rfc3339(start_after)
        if end_before:
            parse_rfc3339(end_before)
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=end_before,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime',
            q='hangoutsMeet'
        ).execute()
        events = events_result.get('items', [])
        meetings = [shape_meeting(e) for e in events]
        logger.info(f"tool=list_meetings action=success count={len(meetings)}")
        return success({"meetings": meetings, "total_count": len(meetings)})
    except ValidationError as ve:
        logger.warning(f"tool=list_meetings validation_error={ve}")
        return failure(str(ve))
    except HttpError as e:
        status = getattr(e.resp, 'status', 0)
        detail = http_error_to_message(status, "Google Calendar API error")
        try:
            error_detail = json.loads(e.content.decode('utf-8'))
        except Exception:
            error_detail = {}
        logger.error(f"tool=list_meetings http_error status={status} msg={detail}")
        return failure(detail, code=str(status or 'http_error'), details=error_detail)
    except Exception as e:
        logger.exception(f"tool=list_meetings unexpected_error={e}")
        return failure("Unexpected server error", code="internal_error")

async def get_meeting_details(event_id: str) -> Dict[str, Any]:
    logger.info(f"tool=get_meeting_details action=start event_id={event_id}")
    try:
        if not event_id:
            return failure("event_id is required")
        access_token = get_auth_token()
        if not access_token:
            return failure("Missing access token", code="unauthorized")
        service = get_calendar_service(access_token)
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        data = shape_meeting(event)
        logger.info(f"tool=get_meeting_details action=success event_id={event_id}")
        return success(data)
    except HttpError as e:
        status = getattr(e.resp, 'status', 0)
        detail = http_error_to_message(status, "Google Calendar API error")
        try:
            error_detail = json.loads(e.content.decode('utf-8'))
        except Exception:
            error_detail = {}
        logger.error(f"tool=get_meeting_details http_error status={status} event_id={event_id}")
        return failure(detail, code=str(status or 'http_error'), details=error_detail)
    except Exception as e:
        logger.exception(f"tool=get_meeting_details unexpected_error={e}")
        return failure("Unexpected server error", code="internal_error")

async def update_meeting(event_id: str, summary: str = None, start_time: str = None, end_time: str = None,
                        attendees: List[str] = None, description: str = None) -> Dict[str, Any]:
    logger.info(f"tool=update_meeting action=start event_id={event_id}")
    try:
        if not event_id:
            return failure("event_id is required")
        if not any([summary, start_time, end_time, attendees, description]):
            return failure("At least one field to update must be provided")
        if start_time and end_time:
            validate_time_window(start_time, end_time)
        elif start_time or end_time:
            # Validate individually
            if start_time:
                parse_rfc3339(start_time)
            if end_time:
                parse_rfc3339(end_time)
        if attendees is not None:
            validate_attendees(attendees)
        access_token = get_auth_token()
        if not access_token:
            return failure("Missing access token", code="unauthorized")
        service = get_calendar_service(access_token)
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        if summary is not None:
            event['summary'] = summary
        if description is not None:
            event['description'] = description
        if start_time is not None:
            event['start'] = {'dateTime': start_time, 'timeZone': 'UTC'}
        if end_time is not None:
            event['end'] = {'dateTime': end_time, 'timeZone': 'UTC'}
        if attendees is not None:
            event['attendees'] = [{'email': email} for email in attendees]
        updated_event = service.events().update(
            calendarId='primary', eventId=event_id, body=event, conferenceDataVersion=1
        ).execute()
        data = shape_meeting(updated_event)
        logger.info(f"tool=update_meeting action=success event_id={event_id}")
        return success(data)
    except ValidationError as ve:
        logger.warning(f"tool=update_meeting validation_error={ve}")
        return failure(str(ve))
    except HttpError as e:
        status = getattr(e.resp, 'status', 0)
        detail = http_error_to_message(status, "Google Calendar API error")
        try:
            error_detail = json.loads(e.content.decode('utf-8'))
        except Exception:
            error_detail = {}
        logger.error(f"tool=update_meeting http_error status={status} event_id={event_id}")
        return failure(detail, code=str(status or 'http_error'), details=error_detail)
    except Exception as e:
        logger.exception(f"tool=update_meeting unexpected_error={e}")
        return failure("Unexpected server error", code="internal_error")

async def delete_meeting(event_id: str) -> Dict[str, Any]:
    logger.info(f"tool=delete_meeting action=start event_id={event_id}")
    try:
        if not event_id:
            return failure("event_id is required")
        access_token = get_auth_token()
        if not access_token:
            return failure("Missing access token", code="unauthorized")
        service = get_calendar_service(access_token)
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        logger.info(f"tool=delete_meeting action=success event_id={event_id}")
        return success({"deleted": True, "event_id": event_id})
    except HttpError as e:
        status = getattr(e.resp, 'status', 0)
        detail = http_error_to_message(status, "Google Calendar API error")
        try:
            error_detail = json.loads(e.content.decode('utf-8'))
        except Exception:
            error_detail = {}
        logger.error(f"tool=delete_meeting http_error status={status} event_id={event_id}")
        return failure(detail, code=str(status or 'http_error'), details=error_detail)
    except Exception as e:
        logger.exception(f"tool=delete_meeting unexpected_error={e}")
        return failure("Unexpected server error", code="internal_error")

@click.command()
@click.option("--port", default=GOOGLE_MEET_MCP_SERVER_PORT, help="Port to listen on for HTTP")
@click.option("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
@click.option("--json-response", is_flag=True, default=False, help="Enable JSON responses for StreamableHTTP instead of SSE streams")
def main(port: int, log_level: str, json_response: bool) -> int:
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    app = Server("google-meet-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
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
                    },
                },
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
            ),
        ]
    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        if name == "google_meet_create_meet":
            summary = arguments.get("summary")
            start_time = arguments.get("start_time")
            end_time = arguments.get("end_time")
            attendees = arguments.get("attendees", [])
            description = arguments.get("description", "")
            result = await create_meet(summary, start_time, end_time, attendees, description)
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "google_meet_list_meetings":
            max_results = arguments.get("max_results", 10)
            start_after = arguments.get("start_after")
            end_before = arguments.get("end_before")
            result = await list_meetings(max_results, start_after, end_before)
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
            result = await update_meeting(event_id, summary, start_time, end_time, attendees, description)
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "google_meet_delete_meeting":
            event_id = arguments.get("event_id")
            if not event_id:
                return [types.TextContent(type="text", text=json.dumps(failure("event_id parameter is required")))]
            result = await delete_meeting(event_id)
            return [types.TextContent(type="text", text=json.dumps(result))]
        return [types.TextContent(type="text", text=json.dumps(failure(f"Unknown tool: {name}", code="unknown_tool")))]
    
    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        
        # Extract auth token from headers
        auth_token = extract_access_token(request)
        
        # Set the auth token in context for this request
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
        event_store=None,  # Stateless mode - can be changed to use an event store
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        logger.info("Handling StreamableHTTP request")
        
        # Extract auth token from headers
        auth_token = extract_access_token(scope)
        
        # Set the auth token in context for this request
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
