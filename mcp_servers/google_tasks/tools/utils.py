from __future__ import annotations

import re
import datetime as _dt
from typing import Any, Dict, Optional

RFC3339_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")


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


def validate_task_data(
    title: str,
    notes: Optional[str] = None,
    due: Optional[str] = None,
    completed: Optional[str] = None,
) -> None:
    """Validate task input data."""
    if not title or not title.strip():
        raise ValidationError("Task title cannot be empty")

    if len(title) > 1024:
        raise ValidationError("Task title too long (max 1024 characters)")

    if notes and len(notes) > 8192:
        raise ValidationError("Task notes too long (max 8192 characters)")

    if due and not is_rfc3339(due):
        raise ValidationError(f"Due date '{due}' must be RFC3339 UTC format")

    if completed and not is_rfc3339(completed):
        raise ValidationError(
            f"Completed date '{completed}' must be RFC3339 UTC format"
        )


def success(data: Any = None, message: str = "Success") -> Dict[str, Any]:
    """Create a success response."""
    result = {"success": True, "message": message}
    if data is not None:
        result["data"] = data
    return result


def failure(message: str, code: str = "error", data: Any = None) -> Dict[str, Any]:
    """Create a failure response."""
    result = {"success": False, "message": message, "code": code}
    if data is not None:
        result["data"] = data
    return result


def shape_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """Shape task data for consistent output."""
    return {
        "kind": task.get("kind"),
        "id": task.get("id"),
        "title": task.get("title", ""),
        "notes": task.get("notes", ""),
        "status": task.get("status", "needsAction"),
        "due": task.get("due"),
        "completed": task.get("completed"),
        "updated": task.get("updated"),
        "position": task.get("position"),
        "parent": task.get("parent"),
        "links": task.get("links", []),
        "deleted": task.get("deleted", False),
        "hidden": task.get("hidden", False),
        "webViewLink": task.get("webViewLink"),
    }


def shape_task_list(task_list: Dict[str, Any]) -> Dict[str, Any]:
    """Shape task list data for consistent output."""
    return {
        "kind": task_list.get("kind"),
        "id": task_list.get("id"),
        "title": task_list.get("title", ""),
        "updated": task_list.get("updated"),
        "self_link": task_list.get("selfLink"),
    }


def http_error_to_message(error: Any) -> str:
    """Convert Google API HTTP error to user-friendly message."""
    if hasattr(error, "resp") and hasattr(error.resp, "status"):
        status = error.resp.status
        if status == 401:
            return "Authentication failed. Please check your access token."
        elif status == 403:
            return "Access denied. Please check your permissions."
        elif status == 404:
            return "Resource not found."
        elif status == 409:
            return "Conflict. The resource may have been modified by another user."
        elif status >= 500:
            return "Server error. Please try again later."

    return f"API error: {str(error)}"
