import contextlib
import base64
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

def extract_access_token(request_or_scope) -> str:
    """Extract access token from x-auth-data header."""
    auth_data = os.getenv("AUTH_DATA")
    
    if not auth_data:
        # Handle different input types (request object for SSE, scope dict for StreamableHTTP)
        if hasattr(request_or_scope, 'headers'):
            # SSE request object
            auth_data = request_or_scope.headers.get(b'x-auth-data')
            if auth_data:
                auth_data = base64.b64decode(auth_data).decode('utf-8')
        elif isinstance(request_or_scope, dict) and 'headers' in request_or_scope:
            # StreamableHTTP scope object
            headers = dict(request_or_scope.get("headers", []))
            auth_data = headers.get(b'x-auth-data')
            if auth_data:
                auth_data = base64.b64decode(auth_data).decode('utf-8')
    
    if not auth_data:
        return ""
    
    try:
        # Parse the JSON auth data to extract access_token
        auth_json = json.loads(auth_data)
        return auth_json.get('access_token', '')
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse auth data JSON: {e}")
        return ""

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

def get_people_service(access_token: str):
    """Create Google People service with access token."""
    credentials = Credentials(token=access_token)
    return build('people', 'v1', credentials=credentials)

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
    recurrence: list[str] | None = None,
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

        # Add recurrence rule if provided
        if recurrence:
            event["recurrence"] = recurrence

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
            "recurrence",
            "recurringEventId",
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
    updated_recurrence: list[str] | None = None,
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
        
        if updated_recurrence is not None:
            # If updated_recurrence is an empty list, remove recurrence (convert to single event)
            # If it has values, update the recurrence rule
            update_fields["recurrence"] = updated_recurrence

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

async def get_current_time() -> Dict[str, Any]:
    """
    Get the current date and time using the user's Google Calendar timezone setting.
    
    This tool provides accurate current time information to prevent hallucinations
    from LLM pre-training data. Always use this tool before scheduling events or
    working with date/time operations.
    """
    logger.info(f"Executing tool: get_current_time")
    try:
        access_token = get_auth_token()
        service = get_calendar_service(access_token)
        
        # Get user's timezone setting from Google Calendar settings - https://developers.google.com/workspace/calendar/api/v3/reference/settings#resource  
        try:
            timezone_setting = service.settings().get(setting='timezone').execute()
            timezone = timezone_setting.get('value', 'UTC')
            logger.info(f"Retrieved user timezone: {timezone}")
        except Exception as e:
            logger.error(f"Failed to retrieve user timezone: {e}")
            raise RuntimeError(f"Failed to retrieve user timezone from Google Calendar: {e}")
        
        # Parse timezone
        try:
            tz = ZoneInfo(timezone)
        except Exception as e:
            logger.error(f"Invalid timezone {timezone}: {e}")
            raise RuntimeError(f"Invalid timezone '{timezone}' received from Google Calendar: {e}")
        
        # Get current time in user's timezone
        now = datetime.now(tz).replace(microsecond=0)
        
        return {
            "datetime": now.strftime("%Y-%m-%dT%H:%M:%S"),
            "timezone": timezone,
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "day_of_week": now.strftime("%A"),
        }
    except Exception as e:
        logger.exception(f"Error executing tool get_current_time: {e}")
        raise e

async def find_free_slots(
    items: list[str] | None = None,
    time_min: str | None = None,
    time_max: str | None = None,
    timezone: str = "UTC",
    min_slot_duration_minutes: int = 30,
) -> Dict[str, Any]:
    """
    Find free and busy time slots for specified calendar users.
    
    Returns a simple structure with busy and free time slots for each user.
    Defaults to the current day if time_min/time_max are omitted.
    """
    logger.info(f"Executing tool: find_free_slots for items: {items}")
    try:
        access_token = get_auth_token()
        service = get_calendar_service(access_token)
        
        # Default to primary calendar if none specified
        if not items:
            items = ["primary"]
        
        # Parse timezone
        try:
            tz = ZoneInfo(timezone)
        except Exception:
            logger.warning(f"Invalid timezone {timezone}, defaulting to UTC")
            tz = ZoneInfo("UTC")
            timezone = "UTC"
        
        # Default to current day in specified timezone if time range not provided
        now = datetime.now(tz)
        if not time_min:
            time_min_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            time_min_dt = datetime.fromisoformat(time_min.replace('Z', '+00:00'))
            if time_min_dt.tzinfo is None:
                time_min_dt = time_min_dt.replace(tzinfo=tz)
            else:
                # Convert to requested timezone
                time_min_dt = time_min_dt.astimezone(tz)
        
        if not time_max:
            time_max_dt = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            time_max_dt = datetime.fromisoformat(time_max.replace('Z', '+00:00'))
            if time_max_dt.tzinfo is None:
                time_max_dt = time_max_dt.replace(tzinfo=tz)
            else:
                # Convert to requested timezone
                time_max_dt = time_max_dt.astimezone(tz)
        
        # Validate time range
        if time_min_dt >= time_max_dt:
            raise ValueError(f"time_min must precede time_max")
        
        # Prepare freebusy query
        body = {
            "timeMin": time_min_dt.isoformat(),
            "timeMax": time_max_dt.isoformat(),
            "timeZone": timezone,
            "items": [{"id": item} for item in items],
        }
        
        # Query freebusy information
        freebusy_result = service.freebusy().query(body=body).execute()
        
        # Process results for each calendar - create simple structure
        calendars = {}
        
        for item in items:
            calendar_data = freebusy_result.get("calendars", {}).get(item, {})
            
            # Check for errors
            if "errors" in calendar_data:
                calendars[item] = {
                    "error": calendar_data["errors"][0].get("reason", "Unknown error"),
                    "busy": [],
                    "free": [],
                }
                continue
            
            busy_periods = calendar_data.get("busy", [])
            
            # Convert busy periods to simple format with timezone
            busy_slots = []
            for busy in busy_periods:
                busy_start = datetime.fromisoformat(busy["start"].replace('Z', '+00:00')).astimezone(tz)
                busy_end = datetime.fromisoformat(busy["end"].replace('Z', '+00:00')).astimezone(tz)
                busy_slots.append({
                    "start": busy_start.isoformat(),
                    "end": busy_end.isoformat(),
                })
            
            # Calculate free slots (gaps between busy periods)
            free_slots = []
            
            # Sort busy periods by start time
            sorted_busy = sorted(
                [(datetime.fromisoformat(b["start"].replace('Z', '+00:00')).astimezone(tz),
                  datetime.fromisoformat(b["end"].replace('Z', '+00:00')).astimezone(tz))
                 for b in busy_periods],
                key=lambda x: x[0]
            )
            
            # Check for free slot at the beginning
            if not sorted_busy or sorted_busy[0][0] > time_min_dt:
                gap_end = sorted_busy[0][0] if sorted_busy else time_max_dt
                duration_minutes = int((gap_end - time_min_dt).total_seconds() / 60)
                if duration_minutes >= min_slot_duration_minutes:
                    free_slots.append({
                        "start": time_min_dt.isoformat(),
                        "end": gap_end.isoformat(),
                    })
            
            # Find gaps between busy periods
            for i in range(len(sorted_busy) - 1):
                gap_start = sorted_busy[i][1]  # End of current busy period
                gap_end = sorted_busy[i + 1][0]  # Start of next busy period
                
                if gap_start < gap_end:
                    duration_minutes = int((gap_end - gap_start).total_seconds() / 60)
                    if duration_minutes >= min_slot_duration_minutes:
                        free_slots.append({
                            "start": gap_start.isoformat(),
                            "end": gap_end.isoformat(),
                        })
            
            # Check for free slot at the end
            if sorted_busy and sorted_busy[-1][1] < time_max_dt:
                gap_start = sorted_busy[-1][1]
                duration_minutes = int((time_max_dt - gap_start).total_seconds() / 60)
                if duration_minutes >= min_slot_duration_minutes:
                    free_slots.append({
                        "start": gap_start.isoformat(),
                        "end": time_max_dt.isoformat(),
                    })
            
            # If no busy periods, the entire time range is free
            if not sorted_busy:
                duration_minutes = int((time_max_dt - time_min_dt).total_seconds() / 60)
                if duration_minutes >= min_slot_duration_minutes:
                    free_slots.append({
                        "start": time_min_dt.isoformat(),
                        "end": time_max_dt.isoformat(),
                    })
            
            calendars[item] = {
                "busy": busy_slots,
                "free": free_slots,
            }
        
        return {
            "calendars": calendars,
        }
        
    except HttpError as e:
        logger.error(f"Google Calendar API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Calendar API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool find_free_slots: {e}")
        raise e

def _warmup_contact_search(access_token: str, contact_type: str):
    """
    Send warmup request with empty query to update the cache.

    According to Google's documentation, searchContacts and otherContacts.search
    require a warmup request before actual searches for better performance.
    See: https://developers.google.com/people/v1/contacts#search_the_users_contacts
    and https://developers.google.com/people/v1/other-contacts#search_the_users_other_contacts

    Note: Creates its own service instance to avoid thread safety issues with httplib2.
    """
    try:
        # Create a separate service instance for this thread
        service = get_people_service(access_token)

        if contact_type == 'personal':
            # Warmup for people.searchContacts
            service.people().searchContacts(
                query="",
                pageSize=1,
                readMask='names'
            ).execute()
            logger.info("Warmup request sent for personal contacts")
        elif contact_type == 'other':
            # Warmup for otherContacts.search
            service.otherContacts().search(
                query="",
                pageSize=1,
                readMask='names'
            ).execute()
            logger.info("Warmup request sent for other contacts")
    except Exception as e:
        # Don't fail if warmup fails, just log it
        logger.warning(f"Warmup request failed for {contact_type} contacts: {e}")

async def search_contacts(
    query: str,
    contact_type: str = "all",
    page_size: int = 10,
    page_token: str | None = None,
    directory_sources: str = "UNSPECIFIED",
) -> Dict[str, Any]:
    """
    Search for contacts by name or email address.

    Supports searching personal contacts, other contact sources, domain directory,
    or all sources simultaneously. When contact_type is 'all' (default), returns
    three separate result sets (personal, other, directory) each with independent
    pagination tokens.
    """
    logger.info(f"Executing tool: search_contacts with query: {query}, contact_type: {contact_type}")
    try:
        access_token = get_auth_token()
        service = get_people_service(access_token)

        # Define the read mask for calendar-relevant person fields
        # Only includes fields necessary for calendar operations (creating events, adding attendees)
        comprehensive_read_mask = 'names,emailAddresses,organizations,phoneNumbers,metadata'

        # Limited read mask for other contacts
        limited_read_mask = 'emailAddresses,metadata,names,phoneNumbers'

        def format_contact(person: Dict[str, Any], contact_type_label: str) -> Dict[str, Any]:
            """Helper function to format a person object into structured contact data."""
            names = person.get('names', [])
            emails = person.get('emailAddresses', [])
            phones = person.get('phoneNumbers', [])
            orgs = person.get('organizations', [])

            return {
                'resourceName': person.get('resourceName', ''),
                'displayName': names[0].get('displayName', 'Unknown') if names else 'Unknown',
                'firstName': names[0].get('givenName', '') if names else '',
                'lastName': names[0].get('familyName', '') if names else '',
                'contactType': contact_type_label,
                'emailAddresses': [
                    {
                        'email': email.get('value', ''),
                        'type': email.get('type', 'other').lower(),
                    }
                    for email in emails
                ],
                'phoneNumbers': [
                    {
                        'number': phone.get('value', ''),
                        'type': phone.get('type', 'other').lower(),
                    }
                    for phone in phones
                ],
                'organizations': [
                    {
                        'name': org.get('name', ''),
                        'title': org.get('title', ''),
                    }
                    for org in orgs
                ],
            }

        if contact_type == 'all':
            # Execute all three searches in parallel (with warmup for personal and other)
            import asyncio

            # Use ThreadPoolExecutor for blocking Google API calls
            from concurrent.futures import ThreadPoolExecutor

            def search_personal():
                # Create separate service instance for thread safety
                personal_service = get_people_service(access_token)
                return personal_service.people().searchContacts(
                    query=query,
                    pageSize=min(page_size, 30),
                    readMask=comprehensive_read_mask,
                ).execute()

            def search_other():
                # Create separate service instance for thread safety
                other_service = get_people_service(access_token)
                return other_service.otherContacts().search(
                    query=query,
                    pageSize=min(page_size, 30),
                    readMask=limited_read_mask,
                ).execute()

            def search_directory():
                # Create separate service instance for thread safety
                directory_service = get_people_service(access_token)
                return directory_service.people().searchDirectoryPeople(
                    query=query,
                    pageSize=min(page_size, 500),
                    readMask=comprehensive_read_mask,
                    sources=['DIRECTORY_SOURCE_TYPE_DOMAIN_PROFILE', 'DIRECTORY_SOURCE_TYPE_DOMAIN_CONTACT'],
                ).execute()

            # Run warmup requests first, then all three searches in parallel
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=5) as executor:
                # Send warmup requests for personal and other contacts
                warmup_personal_future = loop.run_in_executor(
                    executor, _warmup_contact_search, access_token, 'personal'
                )
                warmup_other_future = loop.run_in_executor(
                    executor, _warmup_contact_search, access_token, 'other'
                )

                # Wait for warmup to complete
                await asyncio.gather(warmup_personal_future, warmup_other_future)

                # Now execute actual searches in parallel
                personal_future = loop.run_in_executor(executor, search_personal)
                other_future = loop.run_in_executor(executor, search_other)
                directory_future = loop.run_in_executor(executor, search_directory)

                personal_res, other_res, directory_res = await asyncio.gather(
                    personal_future, other_future, directory_future
                )

            # Process personal results
            personal_results = [
                format_contact(result.get('person', {}), 'personal')
                for result in personal_res.get('results', [])
            ]

            # Process other results
            other_results = [
                format_contact(result.get('person', {}), 'other')
                for result in other_res.get('results', [])
            ]

            # Process directory results
            directory_results = [
                format_contact(person, 'directory')
                for person in directory_res.get('people', [])
            ]

            # Return three independent result sets with pagination info
            return {
                'message': f'Found contacts matching "{query}" from all sources',
                'query': query,
                'contactType': 'all',
                'personal': {
                    'resultCount': len(personal_results),
                    'nextPageToken': personal_res.get('nextPageToken'),
                    'contacts': personal_results,
                },
                'other': {
                    'resultCount': len(other_results),
                    'nextPageToken': other_res.get('nextPageToken'),
                    'contacts': other_results,
                },
                'directory': {
                    'resultCount': len(directory_results),
                    'nextPageToken': directory_res.get('nextPageToken'),
                    'contacts': directory_results,
                },
            }

        elif contact_type == 'personal':
            # Send warmup request before actual search
            import asyncio
            from concurrent.futures import ThreadPoolExecutor

            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=1) as executor:
                await loop.run_in_executor(executor, _warmup_contact_search, access_token, 'personal')

            response = service.people().searchContacts(
                query=query,
                pageSize=min(page_size, 30),
                readMask=comprehensive_read_mask,
            ).execute()

            results = [
                format_contact(result.get('person', {}), 'personal')
                for result in response.get('results', [])
            ]

            return {
                'message': f'Found {len(results)} personal contact(s) matching "{query}"',
                'query': query,
                'contactType': contact_type,
                'resultCount': len(results),
                'nextPageToken': response.get('nextPageToken'),
                'contacts': results,
            }

        elif contact_type == 'other':
            # Send warmup request before actual search
            import asyncio
            from concurrent.futures import ThreadPoolExecutor

            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=1) as executor:
                await loop.run_in_executor(executor, _warmup_contact_search, access_token, 'other')

            response = service.otherContacts().search(
                query=query,
                pageSize=min(page_size, 30),
                readMask=limited_read_mask,
            ).execute()

            results = [
                format_contact(result.get('person', {}), 'other')
                for result in response.get('results', [])
            ]

            return {
                'message': f'Found {len(results)} other contact(s) matching "{query}"',
                'query': query,
                'contactType': contact_type,
                'resultCount': len(results),
                'nextPageToken': response.get('nextPageToken'),
                'contacts': results,
            }

        elif contact_type == 'directory':
            # Map directory sources
            source_map = {
                'UNSPECIFIED': ['DIRECTORY_SOURCE_TYPE_DOMAIN_PROFILE', 'DIRECTORY_SOURCE_TYPE_DOMAIN_CONTACT'],
                'DOMAIN_DIRECTORY': ['DIRECTORY_SOURCE_TYPE_DOMAIN_PROFILE'],
                'DOMAIN_CONTACTS': ['DIRECTORY_SOURCE_TYPE_DOMAIN_CONTACT'],
            }
            sources = source_map.get(directory_sources, source_map['UNSPECIFIED'])

            response = service.people().searchDirectoryPeople(
                query=query,
                pageSize=min(page_size, 500),
                readMask=comprehensive_read_mask,
                sources=sources,
                pageToken=page_token,
            ).execute()

            results = [
                format_contact(person, 'directory')
                for person in response.get('people', [])
            ]

            return {
                'message': f'Found {len(results)} directory contact(s) matching "{query}"',
                'query': query,
                'contactType': contact_type,
                'resultCount': len(results),
                'nextPageToken': response.get('nextPageToken'),
                'contacts': results,
            }

        else:
            raise ValueError(f"Invalid contact_type: {contact_type}. Must be one of: all, personal, other, directory")

    except HttpError as e:
        logger.error(f"Google People API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google People API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool search_contacts: {e}")
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
                name="google_calendar_get_current_time",
                description="Get the accurate current date and time in the user's timezone. CRITICAL: Always call this tool FIRST before any calendar operations (creating, updating, listing, or scheduling events) to prevent using outdated time information. NOTE: If current time information is already provided in the system prompt or context, you do NOT need to call this tool",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_CALENDAR_CONTEXT", "readOnlyHint": True}
                ),
            ),
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
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_CALENDAR_CALENDAR", "readOnlyHint": True}
                ),
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
                            "description": "The datetime when the event starts in ISO 8601 format, e.g., '2024-12-31T15:30:00' or '2024-12-31T15:30:00-07:00' with timezone.",
                        },
                        "end_datetime": {
                            "type": "string",
                            "description": "The datetime when the event ends in ISO 8601 format, e.g., '2024-12-31T17:30:00' or '2024-12-31T17:30:00-07:00' with timezone.",
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
                            "description": "The list of attendee emails. Must be valid email addresses e.g., username@domain.com. You can use google_contact_search_contact tool to find contact emails. YOU MUST NOT assume attendees' email addresses unless it is explicitly provided.",
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
                        "recurrence": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of RRULE, EXRULE, RDATE and EXDATE lines for a recurring event, as specified in RFC5545. Examples: ['RRULE:FREQ=DAILY;COUNT=5'] for 5 days, ['RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR;COUNT=10'] for 10 occurrences on Mon/Wed/Fri, ['RRULE:FREQ=MONTHLY;BYDAY=2TH'] for 2nd Thursday each month. Common frequencies: DAILY, WEEKLY, MONTHLY, YEARLY. Use COUNT for number of occurrences or UNTIL for end date (format: YYYYMMDDTHHMMSSZ).",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_CALENDAR_EVENT"}
                ),
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
                            "description": "Filter by events that end on or after this datetime in ISO 8601 format, e.g., '2024-09-15T09:00:00' or '2024-09-15T09:00:00-07:00' with timezone.",
                        },
                        "max_start_datetime": {
                            "type": "string",
                            "description": "Filter by events that start before this datetime in ISO 8601 format, e.g., '2024-09-16T17:00:00' or '2024-09-16T17:00:00-07:00' with timezone.",
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
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_CALENDAR_EVENT", "readOnlyHint": True}
                ),
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
                            "description": "The updated datetime that the event starts in ISO 8601 format, e.g., '2024-12-31T15:30:00' or '2024-12-31T15:30:00-07:00' with timezone.",
                        },
                        "updated_end_datetime": {
                            "type": "string",
                            "description": "The updated datetime that the event ends in ISO 8601 format, e.g., '2024-12-31T17:30:00' or '2024-12-31T17:30:00-07:00' with timezone.",
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
                            "description": "The list of attendee emails to add. Must be valid email addresses e.g., username@domain.com. You can use google_contact_search_contact tool to find contact emails. YOU MUST NOT assume attendees' email addresses unless it is explicitly provided.",
                        },
                        "attendees_to_remove": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "The list of attendee emails to remove. Must be valid email addresses e.g., username@domain.com. You can use google_contact_search_contact tool to find contact emails. YOU MUST NOT assume attendees' email addresses unless it is explicitly provided.",
                        },
                        "updated_recurrence": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Updated recurrence rules in RRULE format (RFC5545). To convert a recurring event to a single event, pass an empty array []. To add/update recurrence, provide rules like: ['RRULE:FREQ=DAILY;COUNT=5'] for 5 days, ['RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR;COUNT=10'] for 10 occurrences on Mon/Wed/Fri, ['RRULE:FREQ=MONTHLY;BYDAY=2TH'] for 2nd Thursday each month. Common frequencies: DAILY, WEEKLY, MONTHLY, YEARLY. Use COUNT for number of occurrences or UNTIL for end date (format: YYYYMMDDTHHMMSSZ).",
                        },
                        "send_updates": {
                            "type": "string",
                            "description": "Should attendees be notified of the update?",
                            "enum": ["all", "externalOnly", "none"],
                            "default": "all",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_CALENDAR_EVENT"}
                ),
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
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_CALENDAR_EVENT"}
                ),
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
                            "description": "The list of attendee emails to add. Must be valid email addresses e.g., username@domain.com. You can use google_contact_search_contact tool to find contact emails. YOU MUST NOT assume attendees' email addresses unless it is explicitly provided.",
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
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_CALENDAR_EVENT"}
                ),
            ),
            types.Tool(
                name="google_calendar_find_free_slots",
                description="Find both free and busy time slots in Google Calendars for specified calendars within a defined time range (defaults to the current day UTC if time_min/time_max are omitted). Returns busy intervals and calculated free slots by finding gaps between busy periods; time_min must precede time_max if both are provided. This action retrieves free and busy time slots for the specified calendars over a given time period. It analyzes the busy intervals from the calendars and provides calculated free slots based on the gaps in the busy periods. All returned times include timezone information and are formatted in the requested timezone for easy interpretation and scheduling.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "items": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of calendar email addresses to check for availability. Use 'primary' for the user's primary calendar, or specify email addresses like 'user@domain.com'. Defaults to ['primary'] if not provided.",
                        },
                        "time_min": {
                            "type": "string",
                            "description": "The start of the time range to search in ISO 8601 format (e.g., '2024-12-31T09:00:00' or '2024-12-31T09:00:00-07:00' with timezone). If omitted, defaults to the start of the current day (00:00:00) in the specified timezone.",
                        },
                        "time_max": {
                            "type": "string",
                            "description": "The end of the time range to search in ISO 8601 format (e.g., '2024-12-31T17:00:00' or '2024-12-31T17:00:00-07:00' with timezone). If omitted, defaults to the end of the current day (23:59:59) in the specified timezone. Must be after time_min.",
                        },
                        "timezone": {
                            "type": "string",
                            "description": "Timezone for the time range and output (e.g., 'America/Los_Angeles', 'Europe/London', 'Asia/Tokyo'). Defaults to 'UTC'. All returned times will be in this timezone.",
                            "default": "UTC",
                        },
                        "min_slot_duration_minutes": {
                            "type": "integer",
                            "description": "Minimum duration in minutes for a time slot to be considered as a valid free slot. Free slots shorter than this duration will be filtered out. Defaults to 30 minutes.",
                            "default": 30,
                            "minimum": 1,
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_CALENDAR_AVAILABILITY", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="google_calendar_search_contacts",
                description="Search for contacts when you need to know the contact details. Supports searching personal contacts, other contact sources, domain directory, or all sources simultaneously. When contactType is 'all' (default), returns three separate result sets (personal, other, directory) each with independent pagination tokens for flexible paginated access to individual sources.",
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The plain-text search query for contact names, email addresses, phone numbers, etc.",
                        },
                        "contactType": {
                            "type": "string",
                            "description": "Type of contacts to search: 'all' (search all types - returns three separate result sets with independent pagination tokens), 'personal' (your saved contacts), 'other' (other contact sources like Gmail suggestions), or 'directory' (domain directory). Defaults to 'all'.",
                            "enum": ["all", "personal", "other", "directory"],
                            "default": "all",
                        },
                        "pageSize": {
                            "type": "integer",
                            "description": "Number of results to return. For personal/other: max 30, for directory: max 500. Defaults to 10.",
                            "default": 10,
                            "minimum": 1,
                        },
                        "pageToken": {
                            "type": "string",
                            "description": "Page token for pagination (used with directory searches). Optional.",
                        },
                        "directorySources": {
                            "type": "string",
                            "description": "Directory sources to search (only used for directory type): 'UNSPECIFIED' (both domain directory and contacts), 'DOMAIN_DIRECTORY' (domain directory only), or 'DOMAIN_CONTACTS' (domain contacts only). Defaults to 'UNSPECIFIED'.",
                            "enum": ["UNSPECIFIED", "DOMAIN_DIRECTORY", "DOMAIN_CONTACTS"],
                            "default": "UNSPECIFIED",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_CALENDAR_EVENT", "readOnlyHint": True}
                ),
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        if name == "google_calendar_get_current_time":
            try:
                result = await get_current_time()
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
        
        elif name == "google_calendar_list_calendars":
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
                recurrence = arguments.get("recurrence")
                
                result = await create_event(
                    summary, start_datetime, end_datetime, calendar_id,
                    description, location, visibility, attendees, send_updates,
                    add_google_meet, recurrence
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
                updated_recurrence = arguments.get("updated_recurrence")
                send_updates = arguments.get("send_updates", "all")
                
                result = await update_event(
                    event_id, updated_start_datetime, updated_end_datetime,
                    updated_summary, updated_description, updated_location,
                    updated_visibility, attendees_to_add, attendees_to_remove,
                    updated_recurrence, send_updates
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
        
        elif name == "google_calendar_find_free_slots":
            try:
                items = arguments.get("items")
                time_min = arguments.get("time_min")
                time_max = arguments.get("time_max")
                timezone = arguments.get("timezone", "UTC")
                min_slot_duration_minutes = arguments.get("min_slot_duration_minutes", 30)
                
                result = await find_free_slots(
                    items=items,
                    time_min=time_min,
                    time_max=time_max,
                    timezone=timezone,
                    min_slot_duration_minutes=min_slot_duration_minutes
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

        elif name == "google_calendar_search_contacts":
            try:
                query = arguments.get("query")

                if not query:
                    return [
                        types.TextContent(
                            type="text",
                            text="Error: query parameter is required",
                        )
                    ]

                contact_type = arguments.get("contactType", "all")
                page_size = arguments.get("pageSize", 10)
                page_token = arguments.get("pageToken")
                directory_sources = arguments.get("directorySources", "UNSPECIFIED")

                result = await search_contacts(
                    query=query,
                    contact_type=contact_type,
                    page_size=page_size,
                    page_token=page_token,
                    directory_sources=directory_sources
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