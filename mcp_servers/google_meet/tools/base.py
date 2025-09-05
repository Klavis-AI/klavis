from __future__ import annotations

import base64
import datetime
import json
import logging
import os
from contextvars import ContextVar
from typing import Any, Dict, List

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .utils import (
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

# Per-request (or per-stdio session) token storage
auth_token_context: ContextVar[str] = ContextVar("auth_token", default="")


# -------- Token helpers -------- #
def extract_access_token(request_or_scope) -> str:
    """Extract raw access token from:
    1. AUTH_DATA env var containing JSON {"access_token": "..."}
    2. x-auth-data header (base64 encoded JSON) in SSE/HTTP modes
    Returns empty string on failure.
    """
    auth_data = os.getenv("AUTH_DATA")
    if not auth_data and request_or_scope is not None:
        try:
            # Starlette Request object path
            if hasattr(request_or_scope, 'headers'):
                header_val = request_or_scope.headers.get(b'x-auth-data') or request_or_scope.headers.get('x-auth-data')
                if header_val:
                    if isinstance(header_val, bytes):
                        header_val = header_val.decode('utf-8')
                    auth_data = base64.b64decode(header_val).decode('utf-8')
            # ASGI scope dict path
            elif isinstance(request_or_scope, dict) and 'headers' in request_or_scope:
                headers = dict(request_or_scope.get('headers', []))
                header_val = headers.get(b'x-auth-data') or headers.get('x-auth-data')
                if header_val:
                    if isinstance(header_val, bytes):
                        header_val = header_val.decode('utf-8')
                    auth_data = base64.b64decode(header_val).decode('utf-8')
        except Exception as e:  # pragma: no cover (defensive)
            logger.debug(f"Failed to pull x-auth-data header: {e}")

    if not auth_data:
        return ""
    try:
        auth_json = json.loads(auth_data)
        return auth_json.get("access_token", "") or ""
    except Exception as e:  # pragma: no cover (defensive)
        logger.warning(f"Failed to parse AUTH_DATA JSON: {e}")
        return ""


def get_auth_token() -> str:
    try:
        return auth_token_context.get()
    except LookupError:  # pragma: no cover
        return ""


def _calendar_service(access_token: str):
    credentials = Credentials(token=access_token)
    return build('calendar', 'v3', credentials=credentials)


# -------- Tool implementations -------- #
async def create_meet(summary: str, start_time: str, end_time: str, attendees: List[str], description: str = "") -> Dict[str, Any]:
    logger.info(f"tool=create_meet action=start summary='{summary}'")
    try:
        if not summary or not start_time or not end_time or attendees is None:
            return failure("Missing required fields", details={"required": ["summary", "start_time", "end_time", "attendees"]})
        validate_time_window(start_time, end_time)
        validate_attendees(attendees)
        token = get_auth_token()
        if not token:
            return failure("Missing access token", code="unauthorized")
        service = _calendar_service(token)
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
        created = service.events().insert(calendarId='primary', body=event, conferenceDataVersion=1).execute()
        data = shape_meeting(created)
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
    except Exception as e:  # pragma: no cover
        logger.exception(f"tool=create_meet unexpected_error={e}")
        return failure("Unexpected server error", code="internal_error")


async def list_meetings(max_results: int = 10, start_after: str | None = None, end_before: str | None = None) -> Dict[str, Any]:
    logger.info(f"tool=list_meetings action=start max_results={max_results}")
    try:
        if max_results <= 0 or max_results > 100:
            return failure("max_results must be between 1 and 100")
        token = get_auth_token()
        if not token:
            return failure("Missing access token", code="unauthorized")
        service = _calendar_service(token)
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
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        meet_events = []
        for event in events:
            conference_data = event.get('conferenceData', {})
            if conference_data:
                for ep in conference_data.get('entryPoints', []) or []:
                    if ep.get('entryPointType') == 'video' and 'meet.google.com' in ep.get('uri', ''):
                        meet_events.append(event)
                        break
        meetings = [shape_meeting(e) for e in meet_events]
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
    except Exception as e:  # pragma: no cover
        logger.exception(f"tool=list_meetings unexpected_error={e}")
        return failure("Unexpected server error", code="internal_error")


async def get_meeting_details(event_id: str) -> Dict[str, Any]:
    logger.info(f"tool=get_meeting_details action=start event_id={event_id}")
    try:
        if not event_id:
            return failure("event_id is required")
        token = get_auth_token()
        if not token:
            return failure("Missing access token", code="unauthorized")
        service = _calendar_service(token)
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
    except Exception as e:  # pragma: no cover
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
            if start_time:
                parse_rfc3339(start_time)
            if end_time:
                parse_rfc3339(end_time)
        if attendees is not None:
            validate_attendees(attendees)
        token = get_auth_token()
        if not token:
            return failure("Missing access token", code="unauthorized")
        service = _calendar_service(token)
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
        updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event, conferenceDataVersion=1).execute()
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
    except Exception as e:  # pragma: no cover
        logger.exception(f"tool=update_meeting unexpected_error={e}")
        return failure("Unexpected server error", code="internal_error")


async def delete_meeting(event_id: str) -> Dict[str, Any]:
    logger.info(f"tool=delete_meeting action=start event_id={event_id}")
    try:
        if not event_id:
            return failure("event_id is required")
        token = get_auth_token()
        if not token:
            return failure("Missing access token", code="unauthorized")
        service = _calendar_service(token)
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
    except Exception as e:  # pragma: no cover
        logger.exception(f"tool=delete_meeting unexpected_error={e}")
        return failure("Unexpected server error", code="internal_error")


__all__ = [
    "auth_token_context",
    "extract_access_token",
    "get_auth_token",
    "create_meet",
    "list_meetings",
    "list_past_meetings",
    "get_meeting_details",
    "update_meeting",
    "delete_meeting",
    "get_past_meeting_attendees",
]

async def list_past_meetings(max_results: int = 10, since: str | None = None) -> Dict[str, Any]:
    """List past Google Meet meetings that ended before now.

    Args:
        max_results: limit (1-100) after filtering for Meet events.
        since: optional RFC3339 UTC lower bound for event start (timeMin).
    """
    logger.info(f"tool=list_past_meetings action=start max_results={max_results} since={since}")
    try:
        if max_results <= 0 or max_results > 100:
            return failure("max_results must be between 1 and 100")
        if since:
            parse_rfc3339(since)
        token = get_auth_token()
        if not token:
            return failure("Missing access token", code="unauthorized")
        service = _calendar_service(token)

        now_dt = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        page_token = None
        meet_events: list[dict[str, Any]] = []
        fetched_events = 0

        while len(meet_events) < max_results and fetched_events < 5000:
            kwargs = {
                'calendarId': 'primary',
                'singleEvents': True,
                'orderBy': 'startTime',
                'maxResults': 250,
                'timeMax': now_dt.isoformat().replace('+00:00', 'Z'),
            }
            if since:
                kwargs['timeMin'] = since
            if page_token:
                kwargs['pageToken'] = page_token
            events_result = service.events().list(**kwargs).execute()
            events = events_result.get('items', [])
            fetched_events += len(events)
            logger.debug(f"list_past_meetings fetched_batch size={len(events)} total_fetched={fetched_events}")

            for event in events:
                if len(meet_events) >= max_results:
                    break
                end_info = event.get('end', {}) or {}
                end_raw = end_info.get('dateTime') or end_info.get('date')
                if not end_raw:
                    continue
                if len(end_raw) == 10:
                    continue
                try:
                    if end_raw.endswith('Z'):
                        end_dt = datetime.datetime.fromisoformat(end_raw.replace('Z', '+00:00'))
                    else:
                        end_dt = datetime.datetime.fromisoformat(end_raw)
                    if end_dt.tzinfo is None:
                        end_dt = end_dt.replace(tzinfo=datetime.timezone.utc)
                    end_dt_utc = end_dt.astimezone(datetime.timezone.UTC)
                except Exception:
                    continue
                if end_dt_utc > now_dt:
                    continue
                conference_data = event.get('conferenceData', {})
                if not conference_data:
                    continue
                has_meet = False
                for ep in conference_data.get('entryPoints', []) or []:
                    if ep.get('entryPointType') == 'video' and 'meet.google.com' in (ep.get('uri') or ''):
                        has_meet = True
                        break
                if not has_meet:
                    continue
                meet_events.append(event)
            page_token = events_result.get('nextPageToken')
            if not page_token:
                break

        def start_key(ev: dict[str, Any]):
            s = ev.get('start', {}).get('dateTime') or ''
            return s
        meet_events.sort(key=start_key, reverse=True)
        limited = meet_events[:max_results]
        shaped = [shape_meeting(e) for e in limited]
        logger.info(
            "tool=list_past_meetings action=success returned=%d fetched_events=%d pages_exhausted=%s", 
            len(shaped), fetched_events, page_token is None
        )
        return success({
            "meetings": shaped,
            "total_count": len(shaped),
            "debug": {"fetched_events": fetched_events, "raw_collected": len(meet_events)},
        })
    except ValidationError as ve:
        logger.warning(f"tool=list_past_meetings validation_error={ve}")
        return failure(str(ve))
    except HttpError as e:
        status = getattr(e.resp, 'status', 0)
        detail = http_error_to_message(status, "Google Calendar API error")
        try:
            error_detail = json.loads(e.content.decode('utf-8'))
        except Exception:
            error_detail = {}
        logger.error(f"tool=list_past_meetings http_error status={status} msg={detail}")
        return failure(detail, code=str(status or 'http_error'), details=error_detail)
    except Exception as e:  # pragma: no cover
        logger.exception(f"tool=list_past_meetings unexpected_error={e}")
        return failure("Unexpected server error", code="internal_error")


async def get_past_meeting_attendees(event_id: str) -> Dict[str, Any]:
    """Return attendee list (with response statuses) for a past meeting.

    Fails if meeting does not exist or has not yet ended.
    """
    logger.info(f"tool=get_past_meeting_attendees action=start event_id={event_id}")
    try:
        if not event_id:
            return failure("event_id is required")
        token = get_auth_token()
        if not token:
            return failure("Missing access token", code="unauthorized")
        service = _calendar_service(token)
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        end_info = event.get('end', {}) or {}
        end_dt = end_info.get('dateTime') or end_info.get('date')
        if not end_dt:
            return failure("Cannot determine meeting end time", code="no_end_time")
        # Skip all-day events
        if len(end_dt) == 10:
            return failure("Event is all-day or missing precise end time", code="not_supported")
        now = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
        if end_dt > now:
            return failure("Meeting has not ended yet", code="meeting_not_past")
        attendees = event.get('attendees', []) or []
        shaped_attendees = [
            {
                "email": a.get('email', ''),
                "displayName": a.get('displayName', ''),
                "responseStatus": a.get('responseStatus', ''),
                "optional": a.get('optional', False),
            }
            for a in attendees
        ]
        logger.info(f"tool=get_past_meeting_attendees action=success event_id={event_id} count={len(shaped_attendees)}")
        return success({
            "event_id": event_id,
            "summary": event.get('summary', ''),
            "ended": end_dt,
            "attendees": shaped_attendees,
            "meet_url": next(
                (
                    ep.get('uri')
                    for ep in (event.get('conferenceData', {}) or {}).get('entryPoints', []) or []
                    if ep.get('entryPointType') == 'video'
                ),
                "",
            ),
        })
    except HttpError as e:
        status = getattr(e.resp, 'status', 0)
        detail = http_error_to_message(status, "Google Calendar API error")
        try:
            error_detail = json.loads(e.content.decode('utf-8'))
        except Exception:
            error_detail = {}
        logger.error(f"tool=get_past_meeting_attendees http_error status={status} event_id={event_id}")
        return failure(detail, code=str(status or 'http_error'), details=error_detail)
    except Exception as e:  # pragma: no cover
        logger.exception(f"tool=get_past_meeting_attendees unexpected_error={e}")
        return failure("Unexpected server error", code="internal_error")
 