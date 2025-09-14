from __future__ import annotations

import re
import datetime as _dt
from typing import Any, Dict, List, Optional

RFC3339_REGEX = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ValidationError(ValueError):
    """Raised when tool input validation fails."""


def is_rfc3339(value: str) -> bool:
    return bool(RFC3339_REGEX.match(value))


def parse_rfc3339(value: str) -> _dt.datetime:
    if not is_rfc3339(value):
        raise ValidationError(
            f"Value '{value}' must be RFC3339 UTC (e.g. 2025-01-01T10:00:00Z)"
        )
    # Python can parse with strptime; handle optional fractional seconds
    fmt_main = "%Y-%m-%dT%H:%M:%SZ"
    if "." in value:
        base, frac = value[:-1].split(".")
        frac = (frac + "000000")[:6]
        dt = _dt.datetime.strptime(base, "%Y-%m-%dT%H:%M:%S")
        return dt.replace(microsecond=int(frac), tzinfo=_dt.timezone.utc)
    return _dt.datetime.strptime(value, fmt_main).replace(tzinfo=_dt.timezone.utc)


def validate_time_window(start: str, end: str) -> None:
    start_dt = parse_rfc3339(start)
    end_dt = parse_rfc3339(end)
    if end_dt <= start_dt:
        raise ValidationError("end_time must be after start_time")


def validate_attendees(attendees: List[str]) -> None:
    if len(attendees) > 100:
        raise ValidationError("Too many attendees (max 100)")
    for a in attendees:
        if not EMAIL_REGEX.match(a):
            raise ValidationError(f"Invalid attendee email: {a}")


def success(data: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": True, "data": data}


def failure(message: str, code: str = "validation_error", details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    body: Dict[str, Any] = {"success": False, "error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return body


def shape_meeting(event: Dict[str, Any]) -> Dict[str, Any]:
    meet_url = ""
    conference = event.get("conferenceData", {}) or {}
    for ep in conference.get("entryPoints", []) or []:
        if ep.get("entryPointType") == "video" and 'meet.google.com' in (ep.get("uri") or ''):
            meet_url = ep.get("uri", "")
            break
    # Fallback to hangoutLink if no conferenceData video entry point found
    if not meet_url:
        hl = event.get("hangoutLink") or ""
        if 'meet.google.com' in hl:
            meet_url = hl
    return {
        "event_id": event.get("id"),
        "summary": event.get("summary", ""),
        "description": event.get("description", ""),
        "start": event.get("start", {}),
        "end": event.get("end", {}),
        "meet_url": meet_url,
        "attendees": [
            {
                "email": att.get("email", ""),
                "displayName": att.get("displayName", ""),
                "responseStatus": att.get("responseStatus", "")
            }
            for att in event.get("attendees", []) or []
        ],
        "status": event.get("status"),
        "created": event.get("created"),
        "updated": event.get("updated"),
    }


def http_error_to_message(status: int, default: str) -> str:
    mapping = {
        400: "Bad request to Google Calendar API",
        401: "Unauthorized – access token invalid or expired",
        403: "Forbidden – insufficient permissions or missing scopes",
        404: "Event not found",
        409: "Conflict – concurrency issue",
        429: "Rate limit exceeded – retry later",
        500: "Google internal error – retry later",
        503: "Service unavailable – retry later",
    }
    return mapping.get(status, default)
