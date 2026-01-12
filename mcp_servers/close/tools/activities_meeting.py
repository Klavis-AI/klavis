import logging
from typing import Any, List, Optional

from .base import (
    CloseToolExecutionError,
    ToolResponse,
    get_close_client,
    remove_none_values,
    normalize_meeting_activity,
)
from .constants import CLOSE_MAX_LIMIT

logger = logging.getLogger(__name__)


async def list_meetings(
    limit: Optional[int] = None,
    skip: Optional[int] = None,
    lead_id: Optional[str] = None,
    contact_id: Optional[str] = None,
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    date_created__gte: Optional[str] = None,
    date_created__lte: Optional[str] = None,
    starts_at__gte: Optional[str] = None,
    starts_at__lte: Optional[str] = None,
    **kwargs
) -> ToolResponse:
    """
    List meeting activities from Close CRM.
    
    Args:
        limit: Maximum number of results to return (1-200, default 100)
        skip: Number of results to skip for pagination
        lead_id: Filter by lead ID
        contact_id: Filter by contact ID
        user_id: Filter by user ID
        status: Filter by status (upcoming, in-progress, completed, canceled, declined-by-lead, declined-by-org)
        date_created__gte: Filter by creation date (greater than or equal)
        date_created__lte: Filter by creation date (less than or equal)
        starts_at__gte: Filter by start date (greater than or equal, ISO 8601 format)
        starts_at__lte: Filter by start date (less than or equal, ISO 8601 format)
    """
    
    client = get_close_client()
    
    params = remove_none_values({
        "_limit": min(limit, CLOSE_MAX_LIMIT) if limit else 100,
        "_skip": skip,
        "lead_id": lead_id,
        "contact_id": contact_id,
        "user_id": user_id,
        "status": status,
        "date_created__gte": date_created__gte,
        "date_created__lte": date_created__lte,
        "starts_at__gte": starts_at__gte,
        "starts_at__lte": starts_at__lte,
    })
    
    response = await client.get("/activity/meeting/", params=params)
    
    return {
        "meetings": [normalize_meeting_activity(m) for m in response.get("data", [])],
        "hasMore": response.get("has_more", False),
        "totalCount": response.get("total_results"),
    }


async def get_meeting(meeting_id: str) -> ToolResponse:
    """
    Get a specific meeting activity by ID.
    
    Args:
        meeting_id: The ID of the meeting to retrieve
    """
    
    client = get_close_client()
    
    response = await client.get(f"/activity/meeting/{meeting_id}/")
    
    return {"meeting": normalize_meeting_activity(response)}


async def create_meeting(
    lead_id: str,
    starts_at: str,
    ends_at: str,
    status: Optional[str] = None,
    attendees: Optional[List[dict]] = None,
    user_note_html: Optional[str] = None,
    outcome_id: Optional[str] = None,
    user_id: Optional[str] = None,
    date_created: Optional[str] = None,
    **kwargs
) -> ToolResponse:
    """
    Create a new meeting activity in Close CRM.
    
    Args:
        lead_id: The ID of the lead this meeting belongs to
        starts_at: Start time of the meeting (ISO 8601 format)
        ends_at: End time of the meeting (ISO 8601 format)
        status: Meeting status (upcoming, in-progress, completed, canceled, declined-by-lead, declined-by-org)
        attendees: List of attendee objects with contact_id and status (noreply, yes, no, maybe)
        user_note_html: Notes related to the meeting in HTML format
        outcome_id: The ID of a user-defined outcome for the meeting
        user_id: The ID of the user who created the meeting
        date_created: Date the meeting was created (ISO 8601 format)
    """
    
    client = get_close_client()
    
    meeting_data = remove_none_values({
        "lead_id": lead_id,
        "starts_at": starts_at,
        "ends_at": ends_at,
        "status": status,
        "attendees": attendees,
        "user_note_html": user_note_html,
        "outcome_id": outcome_id,
        "user_id": user_id,
        "date_created": date_created,
    })
    
    # Validate status if provided
    if status and status not in ["upcoming", "in-progress", "completed", "canceled", "declined-by-lead", "declined-by-org"]:
        raise CloseToolExecutionError(
            "Status must be one of: upcoming, in-progress, completed, canceled, declined-by-lead, declined-by-org"
        )
    
    # Validate attendees if provided
    if attendees:
        for attendee in attendees:
            if "contact_id" not in attendee:
                raise CloseToolExecutionError("Each attendee must have a contact_id")
            if "status" in attendee and attendee["status"] not in ["noreply", "yes", "no", "maybe"]:
                raise CloseToolExecutionError("Attendee status must be one of: noreply, yes, no, maybe")
    
    response = await client.post("/activity/meeting/", json_data=meeting_data)
    
    return {"meeting": normalize_meeting_activity(response)}


async def update_meeting(
    meeting_id: str,
    starts_at: Optional[str] = None,
    ends_at: Optional[str] = None,
    status: Optional[str] = None,
    attendees: Optional[List[dict]] = None,
    user_note_html: Optional[str] = None,
    outcome_id: Optional[str] = None,
    **kwargs
) -> ToolResponse:
    """
    Update an existing meeting activity.
    
    Args:
        meeting_id: The ID of the meeting to update
        starts_at: Start time of the meeting (ISO 8601 format)
        ends_at: End time of the meeting (ISO 8601 format)
        status: Meeting status
        attendees: List of attendee objects with contact_id and status
        user_note_html: Notes related to the meeting in HTML format
        outcome_id: The ID of a user-defined outcome for the meeting
    """
    
    client = get_close_client()
    
    meeting_data = remove_none_values({
        "starts_at": starts_at,
        "ends_at": ends_at,
        "status": status,
        "attendees": attendees,
        "user_note_html": user_note_html,
        "outcome_id": outcome_id,
    })
    
    if not meeting_data:
        raise CloseToolExecutionError("No update data provided")
    
    # Validate status if provided
    if status and status not in ["upcoming", "in-progress", "completed", "canceled", "declined-by-lead", "declined-by-org"]:
        raise CloseToolExecutionError(
            "Status must be one of: upcoming, in-progress, completed, canceled, declined-by-lead, declined-by-org"
        )
    
    response = await client.put(f"/activity/meeting/{meeting_id}/", json_data=meeting_data)
    
    return {"meeting": normalize_meeting_activity(response)}


async def delete_meeting(meeting_id: str) -> ToolResponse:
    """
    Delete a meeting activity.
    
    Args:
        meeting_id: The ID of the meeting to delete
    """
    
    client = get_close_client()
    
    await client.delete(f"/activity/meeting/{meeting_id}/")
    
    return {"success": True, "meetingId": meeting_id}


async def search_meetings(
    query: str,
    limit: Optional[int] = None,
    **kwargs
) -> ToolResponse:
    """
    Search for meetings in Close CRM.
    
    Args:
        query: Search query string
        limit: Maximum number of results to return (1-200, default 25)
    """
    
    client = get_close_client()
    
    params = remove_none_values({
        "query": query,
        "_limit": min(limit, CLOSE_MAX_LIMIT) if limit else 25,
    })
    
    response = await client.get("/activity/meeting/", params=params)
    
    return {
        "meetings": [normalize_meeting_activity(m) for m in response.get("data", [])],
        "hasMore": response.get("has_more", False),
        "totalCount": response.get("total_results"),
    }
