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
    auth_data = os.getenv("AUTH_DATA")
    if not auth_data and request_or_scope is not None:
        try:
            if hasattr(request_or_scope, 'headers'):
                header_val = request_or_scope.headers.get(b'x-auth-data') or request_or_scope.headers.get('x-auth-data')
                if header_val:
                    if isinstance(header_val, bytes):
                        header_val = header_val.decode('utf-8')
                    auth_data = base64.b64decode(header_val).decode('utf-8')
            elif isinstance(request_or_scope, dict) and 'headers' in request_or_scope:
                headers = dict(request_or_scope.get('headers', []))
                header_val = headers.get(b'x-auth-data') or headers.get('x-auth-data')
                if header_val:
                    if isinstance(header_val, bytes):
                        header_val = header_val.decode('utf-8')
                    auth_data = base64.b64decode(header_val).decode('utf-8')
        except Exception as e:
            logger.debug(f"Failed to pull x-auth-data header: {e}")

    if not auth_data:
        return ""
    try:
        auth_json = json.loads(auth_data)
        return auth_json.get("access_token", "") or ""
    except Exception as e:
        logger.warning(f"Failed to parse AUTH_DATA JSON: {e}")
        return ""


def get_auth_token() -> str:
    try:
        return auth_token_context.get()
    except LookupError:
        return ""


def _calendar_service(access_token: str):
    credentials = Credentials(token=access_token)
    return build('calendar', 'v3', credentials=credentials)


# -------- Tool implementations -------- #
async def create_meet(summary: str, start_time: str, end_time: str, attendees: List[str], description: str = "", notify_attendees: bool = True) -> Dict[str, Any]:
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
        send_updates = 'all' if notify_attendees and attendees else 'none'
        created = service.events().insert(
            calendarId='primary',
            body=event,
            conferenceDataVersion=1,
            sendUpdates=send_updates,
        ).execute()
        data = shape_meeting(created)
        data['invitations_sent'] = bool(attendees) and notify_attendees
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
            orderBy='startTime',
        ).execute()
        events = events_result.get('items', [])
        meet_events = []
        for event in events:
            hangout_link = event.get('hangoutLink') or ""
            conference_data = event.get('conferenceData', {}) or {}
            is_meet = False
            if hangout_link and 'meet.google.com' in hangout_link:
                is_meet = True
            else:
                for ep in conference_data.get('entryPoints', []) or []:
                    if ep.get('entryPointType') == 'video' and 'meet.google.com' in (ep.get('uri') or ''):
                        is_meet = True
                        break
            if is_meet:
                meet_events.append(event)
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
                        attendees: List[str] = None, description: str = None, notify_attendees: bool = True) -> Dict[str, Any]:
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
        original = json.loads(json.dumps(event))  # shallow clone via serialize
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
        changed = False
        for key in ['summary', 'description']:
            if original.get(key) != event.get(key):
                changed = True
                break
        if not changed and (original.get('start') or {}) != (event.get('start') or {}):
            changed = True
        if not changed and (original.get('end') or {}) != (event.get('end') or {}):
            changed = True
        if not changed and attendees is not None:
            orig_emails = sorted([a.get('email') for a in original.get('attendees', []) or []])
            new_emails = sorted([a.get('email') for a in event.get('attendees', []) or []])
            if orig_emails != new_emails:
                changed = True
        if not changed:
            data = shape_meeting(event)
            data['invitations_sent'] = False
            logger.info(f"tool=update_meeting action=noop event_id={event_id}")
            return success(data)
        send_updates = 'all' if notify_attendees else 'none'
        updated_event = service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=event,
            conferenceDataVersion=1,
            sendUpdates=send_updates,
        ).execute()
        data = shape_meeting(updated_event)
        data['invitations_sent'] = notify_attendees
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
        if since:
            time_min_str = since
            lookback_days = None
        else:
            time_min_dt = now_dt - datetime.timedelta(days=30)
            time_min_str = time_min_dt.isoformat().replace('+00:00', 'Z')
            lookback_days = 30
        page_token = None
        meet_events: list[dict[str, Any]] = []
        fetched_events = 0

        def _to_dt(value: str) -> datetime.datetime | None:
            if not value:
                return None
            try:
                if value.endswith('Z'):
                    value = value.replace('Z', '+00:00')
                dt = datetime.datetime.fromisoformat(value)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=datetime.timezone.utc)
                return dt.astimezone(datetime.timezone.utc)
            except Exception:
                return None

        while len(meet_events) < max_results and fetched_events < 3000:
            query = {
                'calendarId': 'primary',
                'singleEvents': True,
                'orderBy': 'startTime',
                'timeMin': time_min_str,
                'timeMax': now_dt.isoformat().replace('+00:00', 'Z'),
                'maxResults': 250,
            }
            if page_token:
                query['pageToken'] = page_token
            resp = service.events().list(**query).execute()
            items = resp.get('items', [])
            fetched_events += len(items)

            for ev in items:
                if len(meet_events) >= max_results:
                    break
                start_raw = (ev.get('start', {}) or {}).get('dateTime') or (ev.get('start', {}) or {}).get('date')
                end_raw = (ev.get('end', {}) or {}).get('dateTime') or (ev.get('end', {}) or {}).get('date')
                if not start_raw or not end_raw or len(start_raw) == 10 or len(end_raw) == 10:
                    continue
                start_dt = _to_dt(start_raw)
                end_dt = _to_dt(end_raw)
                if not start_dt or not end_dt:
                    continue
                if end_dt > now_dt:
                    continue
                hangout_link = ev.get('hangoutLink') or ''
                if 'meet.google.com' in hangout_link:
                    meet_events.append(ev)
                    continue
                conf = ev.get('conferenceData', {}) or {}
                for ep in conf.get('entryPoints', []) or []:
                    if ep.get('entryPointType') == 'video' and 'meet.google.com' in (ep.get('uri') or ''):
                        meet_events.append(ev)
                        break
            page_token = resp.get('nextPageToken')
            if not page_token:
                break

        # Sort newest (latest start) first
        meet_events.sort(key=lambda e: (e.get('start', {}) or {}).get('dateTime') or '', reverse=True)
        shaped = [shape_meeting(e) for e in meet_events[:max_results]]
        logger.info(
            "tool=list_past_meetings action=success returned=%d fetched_events=%d pages_exhausted=%s", 
            len(shaped), fetched_events, page_token is None
        )
        return success({
            "meetings": shaped,
            "total_count": len(shaped),
            "debug": {
                "fetched_events": fetched_events,
                "raw_collected": len(meet_events),
                "timeMin": time_min_str,
                "lookback_days": lookback_days,
            },
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
        meet_url = next(
            (
                ep.get('uri')
                for ep in (event.get('conferenceData', {}) or {}).get('entryPoints', []) or []
                if ep.get('entryPointType') == 'video' and 'meet.google.com' in (ep.get('uri') or '')
            ),
            event.get('hangoutLink', '') or ''
        )
        if 'meet.google.com' not in meet_url:
            meet_url = ''
        return success({
            "event_id": event_id,
            "summary": event.get('summary', ''),
            "ended": end_dt,
            "attendees": shaped_attendees,
            "meet_url": meet_url,
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
 