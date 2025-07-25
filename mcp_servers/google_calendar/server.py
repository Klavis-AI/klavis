import contextlib
import logging
import os
import json
import uuid
from collections.abc import AsyncIterator
from typing import Any, Dict
from contextvars import ContextVar
from enum import Enum
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

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

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

GOOGLE_CALENDAR_MCP_SERVER_PORT = int(os.getenv("GOOGLE_CALENDAR_MCP_SERVER_PORT", "5000"))

# Context variable to store the access token for each request
auth_token_context: ContextVar[str] = ContextVar('auth_token')

# Define enums that are referenced in context.py
class EventVisibility(Enum):
    DEFAULT = "default"
    PUBLIC = "public"
    PRIVATE = "private"

class SendUpdatesOptions(Enum):
    ALL = "all"
    EXTERNAL_ONLY = "externalOnly"
    NONE = "none"

# Error class for retryable errors
class RetryableToolError(Exception):
    def __init__(self, message: str, additional_prompt_content: str = "", retry_after_ms: int = 1000, developer_message: str = ""):
        super().__init__(message)
        self.additional_prompt_content = additional_prompt_content
        self.retry_after_ms = retry_after_ms
        self.developer_message = developer_message

def get_calendar_service(access_token: str):
    """Create Google Calendar service with access token."""
    credentials = Credentials(token=access_token)
    return build('calendar', 'v3', credentials=credentials)

def get_auth_token() -> str:
    """Get the authentication token from context."""
    try:
        return auth_token_context.get()
    except LookupError:
        raise RuntimeError("Authentication token not found in request context")

def parse_datetime(datetime_string: str, time_zone: str) -> datetime:
    """Parse datetime string to datetime object with timezone."""
    try:
        # Try to parse as ISO format
        dt = datetime.fromisoformat(datetime_string.replace('Z', '+00:00'))
        # Convert to specified timezone if not already timezone-aware
        if dt.tzinfo is None:
            tz = ZoneInfo(time_zone)
            dt = dt.replace(tzinfo=tz)
        return dt
    except ValueError:
        raise ValueError(f"Invalid datetime format: {datetime_string}")

# Context class to mock the context.get_auth_token_or_empty() calls
class Context:
    def get_auth_token_or_empty(self) -> str:
        return get_auth_token()

context = Context()

async def list_calendars(
    max_results: int = 10,
    show_deleted: bool = False,
    show_hidden: bool = False,
    next_page_token: str | None = None,
) -> Dict[str, Any]:
    """List all calendars accessible by the user."""
    logger.info(f"Executing tool: list_calendars with max_results: {max_results}")
    try:
        access_token = get_auth_token()
        service = get_calendar_service(access_token)
        
        max_results = max(1, min(max_results, 250))
        calendars = (
            service.calendarList()
            .list(
                pageToken=next_page_token,
                showDeleted=show_deleted,
                showHidden=show_hidden,
                maxResults=max_results,
            )
            .execute()
        )

        items = calendars.get("items", [])
        keys = ["description", "id", "summary", "timeZone"]
        relevant_items = [{k: i.get(k) for k in keys if i.get(k)} for i in items]
        return {
            "next_page_token": calendars.get("nextPageToken"),
            "num_calendars": len(relevant_items),
            "calendars": relevant_items,
        }
    except HttpError as e:
        logger.error(f"Google Calendar API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Calendar API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool list_calendars: {e}")
        raise e

async def create_event(
    summary: str,
    start_datetime: str,
    end_datetime: str,
    calendar_id: str = "primary",
    description: str | None = None,
    location: str | None = None,
    visibility: str = "default",
    attendees: list[str] | None = None,
    send_updates: str = "all",
    add_google_meet: bool = False,
) -> Dict[str, Any]:
    """Create a new event/meeting/sync/meetup in the specified calendar."""
    logger.info(f"Executing tool: create_event with summary: {summary}")
    try:
        access_token = get_auth_token()
        service = get_calendar_service(access_token)

        # Get the calendar's time zone
        calendar = service.calendars().get(calendarId=calendar_id).execute()
        time_zone = calendar["timeZone"]

        # Parse datetime strings
        start_dt = parse_datetime(start_datetime, time_zone)
        end_dt = parse_datetime(end_datetime, time_zone)

        event: Dict[str, Any] = {
            "summary": summary,
            "description": description,
            "location": location,
            "start": {"dateTime": start_dt.isoformat(), "timeZone": time_zone},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": time_zone},
            "visibility": visibility,
        }

        if attendees:
            event["attendees"] = [{"email": email} for email in attendees]

        # Add Google Meet conference if requested
        if add_google_meet:
            event["conferenceData"] = {
                "createRequest": {
                    "requestId": str(uuid.uuid4()),
                    "conferenceSolutionKey": {
                        "type": "hangoutsMeet"
                    }
                }
            }

        # Set conferenceDataVersion to 1 when creating conferences
        conference_data_version = 1 if add_google_meet else 0

        created_event = service.events().insert(
            calendarId=calendar_id, 
            body=event,
            sendUpdates=send_updates,
            conferenceDataVersion=conference_data_version
        ).execute()
        return {"event": created_event}
    except HttpError as e:
        logger.error(f"Google Calendar API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Calendar API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool create_event: {e}")
        raise e

async def list_events(
    min_end_datetime: str,
    max_start_datetime: str,
    calendar_id: str = "primary",
    max_results: int = 10,
) -> Dict[str, Any]:
    """List events from the specified calendar within the given datetime range."""
    logger.info(f"Executing tool: list_events from {min_end_datetime} to {max_start_datetime}")
    try:
        access_token = get_auth_token()
        service = get_calendar_service(access_token)

        # Get the calendar's time zone
        calendar = service.calendars().get(calendarId=calendar_id).execute()
        time_zone = calendar["timeZone"]

        # Parse datetime strings
        min_end_dt = parse_datetime(min_end_datetime, time_zone)
        max_start_dt = parse_datetime(max_start_datetime, time_zone)

        if min_end_dt > max_start_dt:
            min_end_dt, max_start_dt = max_start_dt, min_end_dt

        events_result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=min_end_dt.isoformat(),
                timeMax=max_start_dt.isoformat(),
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        items_keys = [
            "attachments",
            "attendees",
            "creator",
            "description",
            "end",
            "eventType",
            "htmlLink",
            "id",
            "location",
            "organizer",
            "start",
            "summary",
            "visibility",
        ]

        events = [
            {key: event[key] for key in items_keys if key in event}
            for event in events_result.get("items", [])
        ]

        return {"events_count": len(events), "events": events}
    except HttpError as e:
        logger.error(f"Google Calendar API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Calendar API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool list_events: {e}")
        raise e

async def update_event(
    event_id: str,
    updated_start_datetime: str | None = None,
    updated_end_datetime: str | None = None,
    updated_summary: str | None = None,
    updated_description: str | None = None,
    updated_location: str | None = None,
    updated_visibility: str | None = None,
    attendees_to_add: list[str] | None = None,
    attendees_to_remove: list[str] | None = None,
    send_updates: str = "all",
) -> str:
    """Update an existing event in the specified calendar with the provided details."""
    logger.info(f"Executing tool: update_event with event_id: {event_id}")
    try:
        access_token = get_auth_token()
        service = get_calendar_service(access_token)

        calendar = service.calendars().get(calendarId="primary").execute()
        time_zone = calendar["timeZone"]

        try:
            event = service.events().get(calendarId="primary", eventId=event_id).execute()
        except HttpError:
            valid_events_with_id = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=(datetime.now() - timedelta(days=2)).isoformat(),
                    timeMax=(datetime.now() + timedelta(days=365)).isoformat(),
                    maxResults=50,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            raise RuntimeError(f"Event with ID {event_id} not found. Available events: {valid_events_with_id}")

        update_fields = {}
        
        if updated_start_datetime:
            update_fields["start"] = {"dateTime": updated_start_datetime, "timeZone": time_zone}
        
        if updated_end_datetime:
            update_fields["end"] = {"dateTime": updated_end_datetime, "timeZone": time_zone}
        
        if updated_summary:
            update_fields["summary"] = updated_summary
        
        if updated_description:
            update_fields["description"] = updated_description
        
        if updated_location:
            update_fields["location"] = updated_location
        
        if updated_visibility:
            update_fields["visibility"] = updated_visibility

        event.update({k: v for k, v in update_fields.items() if v is not None})

        if attendees_to_remove:
            event["attendees"] = [
                attendee
                for attendee in event.get("attendees", [])
                if attendee.get("email", "").lower()
                not in [email.lower() for email in attendees_to_remove]
            ]

        if attendees_to_add:
            existing_emails = {
                attendee.get("email", "").lower() for attendee in event.get("attendees", [])
            }
            new_attendees = [
                {"email": email}
                for email in attendees_to_add
                if email.lower() not in existing_emails
            ]
            event["attendees"] = event.get("attendees", []) + new_attendees

        updated_event = (
            service.events()
            .update(
                calendarId="primary",
                eventId=event_id,
                sendUpdates=send_updates,
                body=event,
            )
            .execute()
        )
        return (
            f"Event with ID {event_id} successfully updated at {updated_event['updated']}. "
            f"View updated event at {updated_event['htmlLink']}"
        )
    except HttpError as e:
        logger.error(f"Google Calendar API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Calendar API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool update_event: {e}")
        raise e

async def add_attendees_to_event(
    event_id: str,
    attendees: list[str],
    calendar_id: str = "primary",
    send_updates: str = "all",
) -> str:
    """Add attendees to an existing event in Google Calendar."""
    logger.info(f"Executing tool: add_attendees_to_event with event_id: {event_id}")
    try:
        access_token = get_auth_token()
        service = get_calendar_service(access_token)

        # Get the existing event
        try:
            event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        except HttpError:
            valid_events_with_id = (
                service.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=(datetime.now() - timedelta(days=2)).isoformat(),
                    timeMax=(datetime.now() + timedelta(days=365)).isoformat(),
                    maxResults=50,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            raise RuntimeError(f"Event with ID {event_id} not found. Available events: {valid_events_with_id}")

        # Get existing attendee emails (case-insensitive)
        existing_emails = {
            attendee.get("email", "").lower() for attendee in event.get("attendees", [])
        }

        # Filter out emails that are already attendees
        new_attendees = [
            {"email": email}
            for email in attendees
            if email.lower() not in existing_emails
        ]

        if not new_attendees:
            existing_attendee_list = [attendee.get("email", "") for attendee in event.get("attendees", [])]
            return (
                f"No new attendees were added to event '{event_id}' because all specified emails "
                f"are already attendees. Current attendees: {existing_attendee_list}"
            )

        # Add new attendees to the event
        event["attendees"] = event.get("attendees", []) + new_attendees

        # Update the event
        updated_event = (
            service.events()
            .update(
                calendarId=calendar_id,
                eventId=event_id,
                sendUpdates=send_updates,
                body=event,
            )
            .execute()
        )

        added_emails = [attendee["email"] for attendee in new_attendees]
        notification_message = ""
        if send_updates == "all":
            notification_message = "Notifications were sent to all attendees."
        elif send_updates == "externalOnly":
            notification_message = "Notifications were sent to external attendees only."
        elif send_updates == "none":
            notification_message = "No notifications were sent to attendees."

        return (
            f"Successfully added {len(new_attendees)} new attendees to event '{event_id}': {', '.join(added_emails)}. "
            f"{notification_message} View updated event at {updated_event['htmlLink']}"
        )
    except HttpError as e:
        logger.error(f"Google Calendar API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Calendar API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool add_attendees_to_event: {e}")
        raise e

async def delete_event(
    event_id: str,
    calendar_id: str = "primary",
    send_updates: str = "all",
) -> str:
    """Delete an event from Google Calendar."""
    logger.info(f"Executing tool: delete_event with event_id: {event_id}")
    try:
        access_token = get_auth_token()
        service = get_calendar_service(access_token)

        service.events().delete(
            calendarId=calendar_id, eventId=event_id, sendUpdates=send_updates
        ).execute()

        notification_message = ""
        if send_updates == "all":
            notification_message = "Notifications were sent to all attendees."
        elif send_updates == "externalOnly":
            notification_message = "Notifications were sent to external attendees only."
        elif send_updates == "none":
            notification_message = "No notifications were sent to attendees."

        return (
            f"Event with ID '{event_id}' successfully deleted from calendar '{calendar_id}'. "
            f"{notification_message}"
        )
    except HttpError as e:
        logger.error(f"Google Calendar API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Calendar API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool delete_event: {e}")
        raise e

@click.command()
@click.option("--port", default=GOOGLE_CALENDAR_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("google-calendar-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="google_calendar_list_calendars",
                description="List all calendars accessible by the user.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "max_results": {
                            "type": "integer",
                            "description": "The maximum number of calendars to return. Up to 250 calendars, defaults to 10.",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 250,
                        },
                        "show_deleted": {
                            "type": "boolean",
                            "description": "Whether to show deleted calendars. Defaults to False",
                            "default": False,
                        },
                        "show_hidden": {
                            "type": "boolean",
                            "description": "Whether to show hidden calendars. Defaults to False",
                            "default": False,
                        },
                        "next_page_token": {
                            "type": "string",
                            "description": "The token to retrieve the next page of calendars. Optional.",
                        },
                    },
                },
            ),
            types.Tool(
                name="google_calendar_create_event",
                description="Create a new event/meeting/sync/meetup in the specified calendar.",
                inputSchema={
                    "type": "object",
                    "required": ["summary", "start_datetime", "end_datetime"],
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "The title of the event",
                        },
                        "start_datetime": {
                            "type": "string",
                            "description": "The datetime when the event starts in ISO 8601 format, e.g., '2024-12-31T15:30:00'.",
                        },
                        "end_datetime": {
                            "type": "string",
                            "description": "The datetime when the event ends in ISO 8601 format, e.g., '2024-12-31T17:30:00'.",
                        },
                        "calendar_id": {
                            "type": "string",
                            "description": "The ID of the calendar to create the event in, usually 'primary'.",
                            "default": "primary",
                        },
                        "description": {
                            "type": "string",
                            "description": "The description of the event",
                        },
                        "location": {
                            "type": "string",
                            "description": "The location of the event",
                        },
                        "visibility": {
                            "type": "string",
                            "description": "The visibility of the event",
                            "enum": ["default", "public", "private"],
                            "default": "default",
                        },
                        "attendees": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "The list of attendee emails. Must be valid email addresses e.g., username@domain.com.",
                        },
                        "send_updates": {
                            "type": "string",
                            "description": "Should attendees be notified of the update?",
                            "enum": ["all", "externalOnly", "none"],
                            "default": "all",
                        },
                        "add_google_meet": {
                            "type": "boolean",
                            "description": "Whether to add a Google Meet conference to the event.",
                            "default": False,
                        },
                    },
                },
            ),
            types.Tool(
                name="google_calendar_list_events",
                description="List events from the specified calendar within the given datetime range.",
                inputSchema={
                    "type": "object",
                    "required": ["min_end_datetime", "max_start_datetime"],
                    "properties": {
                        "min_end_datetime": {
                            "type": "string",
                            "description": "Filter by events that end on or after this datetime in ISO 8601 format, e.g., '2024-09-15T09:00:00'.",
                        },
                        "max_start_datetime": {
                            "type": "string",
                            "description": "Filter by events that start before this datetime in ISO 8601 format, e.g., '2024-09-16T17:00:00'.",
                        },
                        "calendar_id": {
                            "type": "string",
                            "description": "The ID of the calendar to list events from",
                            "default": "primary",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "The maximum number of events to return",
                            "default": 10,
                        },
                    },
                },
            ),
            types.Tool(
                name="google_calendar_update_event",
                description="Update an existing event in the specified calendar with the provided details.",
                inputSchema={
                    "type": "object",
                    "required": ["event_id"],
                    "properties": {
                        "event_id": {
                            "type": "string",
                            "description": "The ID of the event to update",
                        },
                        "updated_start_datetime": {
                            "type": "string",
                            "description": "The updated datetime that the event starts in ISO 8601 format, e.g., '2024-12-31T15:30:00'.",
                        },
                        "updated_end_datetime": {
                            "type": "string",
                            "description": "The updated datetime that the event ends in ISO 8601 format, e.g., '2024-12-31T17:30:00'.",
                        },
                        "updated_summary": {
                            "type": "string",
                            "description": "The updated title of the event",
                        },
                        "updated_description": {
                            "type": "string",
                            "description": "The updated description of the event",
                        },
                        "updated_location": {
                            "type": "string",
                            "description": "The updated location of the event",
                        },
                        "updated_visibility": {
                            "type": "string",
                            "description": "The visibility of the event",
                            "enum": ["default", "public", "private"],
                        },
                        "attendees_to_add": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "The list of attendee emails to add. Must be valid email addresses e.g., username@domain.com.",
                        },
                        "attendees_to_remove": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "The list of attendee emails to remove. Must be valid email addresses e.g., username@domain.com.",
                        },
                        "send_updates": {
                            "type": "string",
                            "description": "Should attendees be notified of the update?",
                            "enum": ["all", "externalOnly", "none"],
                            "default": "all",
                        },
                    },
                },
            ),
            types.Tool(
                name="google_calendar_delete_event",
                description="Delete an event from Google Calendar.",
                inputSchema={
                    "type": "object",
                    "required": ["event_id"],
                    "properties": {
                        "event_id": {
                            "type": "string",
                            "description": "The ID of the event to delete",
                        },
                        "calendar_id": {
                            "type": "string",
                            "description": "The ID of the calendar containing the event",
                            "default": "primary",
                        },
                        "send_updates": {
                            "type": "string",
                            "description": "Specifies which attendees to notify about the deletion",
                            "enum": ["all", "externalOnly", "none"],
                            "default": "all",
                        },
                    },
                },
            ),
            types.Tool(
                name="google_calendar_add_attendees_to_event",
                description="Add attendees to an existing event in Google Calendar.",
                inputSchema={
                    "type": "object",
                    "required": ["event_id", "attendees"],
                    "properties": {
                        "event_id": {
                            "type": "string",
                            "description": "The ID of the event to add attendees to",
                        },
                        "attendees": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "The list of attendee emails to add. Must be valid email addresses e.g., username@domain.com.",
                        },
                        "calendar_id": {
                            "type": "string",
                            "description": "The ID of the calendar containing the event",
                            "default": "primary",
                        },
                        "send_updates": {
                            "type": "string",
                            "description": "Specifies which attendees to notify about the addition",
                            "enum": ["all", "externalOnly", "none"],
                            "default": "all",
                        },
                    },
                },
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        if name == "google_calendar_list_calendars":
            try:
                max_results = arguments.get("max_results", 10)
                show_deleted = arguments.get("show_deleted", False)
                show_hidden = arguments.get("show_hidden", False)
                next_page_token = arguments.get("next_page_token")
                
                result = await list_calendars(max_results, show_deleted, show_hidden, next_page_token)
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
        
        elif name == "google_calendar_create_event":
            try:
                summary = arguments.get("summary")
                start_datetime = arguments.get("start_datetime")
                end_datetime = arguments.get("end_datetime")
                
                if not summary or not start_datetime or not end_datetime:
                    return [
                        types.TextContent(
                            type="text",
                            text="Error: summary, start_datetime and end_datetime parameters are required",
                        )
                    ]
                
                calendar_id = arguments.get("calendar_id", "primary")
                description = arguments.get("description")
                location = arguments.get("location")
                visibility = arguments.get("visibility", "default")
                attendees = arguments.get("attendees")
                send_updates = arguments.get("send_updates", "all")
                add_google_meet = arguments.get("add_google_meet", False)
                
                result = await create_event(
                    summary, start_datetime, end_datetime, calendar_id,
                    description, location, visibility, attendees, send_updates,
                    add_google_meet
                )
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
        
        elif name == "google_calendar_list_events":
            try:
                min_end_datetime = arguments.get("min_end_datetime")
                max_start_datetime = arguments.get("max_start_datetime")
                
                if not min_end_datetime or not max_start_datetime:
                    return [
                        types.TextContent(
                            type="text",
                            text="Error: min_end_datetime and max_start_datetime parameters are required",
                        )
                    ]
                
                calendar_id = arguments.get("calendar_id", "primary")
                max_results = arguments.get("max_results", 10)
                
                result = await list_events(min_end_datetime, max_start_datetime, calendar_id, max_results)
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
        
        elif name == "google_calendar_update_event":
            try:
                event_id = arguments.get("event_id")
                
                if not event_id:
                    return [
                        types.TextContent(
                            type="text",
                            text="Error: event_id parameter is required",
                        )
                    ]
                
                updated_start_datetime = arguments.get("updated_start_datetime")
                updated_end_datetime = arguments.get("updated_end_datetime")
                updated_summary = arguments.get("updated_summary")
                updated_description = arguments.get("updated_description")
                updated_location = arguments.get("updated_location")
                updated_visibility = arguments.get("updated_visibility")
                attendees_to_add = arguments.get("attendees_to_add")
                attendees_to_remove = arguments.get("attendees_to_remove")
                send_updates = arguments.get("send_updates", "all")
                
                result = await update_event(
                    event_id, updated_start_datetime, updated_end_datetime,
                    updated_summary, updated_description, updated_location,
                    updated_visibility, attendees_to_add, attendees_to_remove,
                    send_updates
                )
                return [
                    types.TextContent(
                        type="text",
                        text=result,
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
        
        elif name == "google_calendar_delete_event":
            try:
                event_id = arguments.get("event_id")
                
                if not event_id:
                    return [
                        types.TextContent(
                            type="text",
                            text="Error: event_id parameter is required",
                        )
                    ]
                
                calendar_id = arguments.get("calendar_id", "primary")
                send_updates = arguments.get("send_updates", "all")
                
                result = await delete_event(event_id, calendar_id, send_updates)
                return [
                    types.TextContent(
                        type="text",
                        text=result,
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
        
        elif name == "google_calendar_add_attendees_to_event":
            try:
                event_id = arguments.get("event_id")
                attendees = arguments.get("attendees")
                
                if not event_id:
                    return [
                        types.TextContent(
                            type="text",
                            text="Error: event_id parameter is required",
                        )
                    ]
                
                if not attendees:
                    return [
                        types.TextContent(
                            type="text",
                            text="Error: attendees parameter is required",
                        )
                    ]
                
                calendar_id = arguments.get("calendar_id", "primary")
                send_updates = arguments.get("send_updates", "all")
                
                result = await add_attendees_to_event(event_id, attendees, calendar_id, send_updates)
                return [
                    types.TextContent(
                        type="text",
                        text=result,
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