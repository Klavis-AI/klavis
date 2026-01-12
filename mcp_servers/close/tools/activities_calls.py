import logging
from typing import Any, List, Optional

from .base import (
    CloseToolExecutionError,
    ToolResponse,
    get_close_client,
    remove_none_values,
    normalize_call_activity,
)
from .constants import CLOSE_MAX_LIMIT

logger = logging.getLogger(__name__)


async def list_calls(
    limit: Optional[int] = None,
    skip: Optional[int] = None,
    lead_id: Optional[str] = None,
    contact_id: Optional[str] = None,
    user_id: Optional[str] = None,
    direction: Optional[str] = None,
    disposition: Optional[str] = None,
    date_created__gte: Optional[str] = None,
    date_created__lte: Optional[str] = None,
    **kwargs
) -> ToolResponse:
    """
    List call activities from Close CRM.
    
    Args:
        limit: Maximum number of results to return (1-200, default 100)
        skip: Number of results to skip for pagination
        lead_id: Filter by lead ID
        contact_id: Filter by contact ID
        user_id: Filter by user ID
        direction: Filter by direction ('inbound' or 'outbound')
        disposition: Filter by disposition (e.g., 'answered', 'voicemail', 'busy', 'no-answer')
        date_created__gte: Filter by creation date (greater than or equal)
        date_created__lte: Filter by creation date (less than or equal)
    """
    
    client = get_close_client()
    
    params = remove_none_values({
        "_limit": min(limit, CLOSE_MAX_LIMIT) if limit else 100,
        "_skip": skip,
        "lead_id": lead_id,
        "contact_id": contact_id,
        "user_id": user_id,
        "direction": direction,
        "disposition": disposition,
        "date_created__gte": date_created__gte,
        "date_created__lte": date_created__lte,
    })
    
    response = await client.get("/activity/call/", params=params)
    
    return {
        "calls": [normalize_call_activity(c) for c in response.get("data", [])],
        "hasMore": response.get("has_more", False),
        "totalCount": response.get("total_results"),
    }


async def get_call(call_id: str) -> ToolResponse:
    """
    Get a specific call activity by ID.
    
    Args:
        call_id: The ID of the call to retrieve
    """
    
    client = get_close_client()
    
    response = await client.get(f"/activity/call/{call_id}/")
    
    return {"call": normalize_call_activity(response)}


async def create_call(
    lead_id: str,
    direction: str,
    phone: Optional[str] = None,
    disposition: Optional[str] = None,
    duration: Optional[int] = None,
    note: Optional[str] = None,
    contact_id: Optional[str] = None,
    user_id: Optional[str] = None,
    voicemail_url: Optional[str] = None,
    recording_url: Optional[str] = None,
    date_created: Optional[str] = None,
    **kwargs
) -> ToolResponse:
    """
    Create a new call activity in Close CRM.
    
    Args:
        lead_id: The ID of the lead this call belongs to
        direction: Call direction ('inbound' or 'outbound')
        phone: Phone number
        disposition: Call disposition (e.g., 'answered', 'voicemail', 'busy', 'no-answer')
        duration: Call duration in seconds
        note: Notes about the call
        contact_id: The ID of the contact
        user_id: The ID of the user who made/received the call
        voicemail_url: URL to voicemail recording
        recording_url: URL to call recording
        date_created: Date the call was created (ISO 8601 format)
    """
    
    client = get_close_client()
    
    call_data = remove_none_values({
        "lead_id": lead_id,
        "direction": direction,
        "phone": phone,
        "disposition": disposition,
        "duration": duration,
        "note": note,
        "contact_id": contact_id,
        "user_id": user_id,
        "voicemail_url": voicemail_url,
        "recording_url": recording_url,
        "date_created": date_created,
    })
    
    if direction not in ["inbound", "outbound"]:
        raise CloseToolExecutionError("Direction must be 'inbound' or 'outbound'")
    
    response = await client.post("/activity/call/", json_data=call_data)
    
    return {"call": normalize_call_activity(response)}


async def update_call(
    call_id: str,
    disposition: Optional[str] = None,
    duration: Optional[int] = None,
    note: Optional[str] = None,
    phone: Optional[str] = None,
    voicemail_url: Optional[str] = None,
    recording_url: Optional[str] = None,
    **kwargs
) -> ToolResponse:
    """
    Update an existing call activity.
    
    Args:
        call_id: The ID of the call to update
        disposition: Call disposition
        duration: Call duration in seconds
        note: Notes about the call
        phone: Phone number
        voicemail_url: URL to voicemail recording
        recording_url: URL to call recording
    """
    
    client = get_close_client()
    
    call_data = remove_none_values({
        "disposition": disposition,
        "duration": duration,
        "note": note,
        "phone": phone,
        "voicemail_url": voicemail_url,
        "recording_url": recording_url,
    })
    
    if not call_data:
        raise CloseToolExecutionError("No update data provided")
    
    response = await client.put(f"/activity/call/{call_id}/", json_data=call_data)
    
    return {"call": normalize_call_activity(response)}


async def delete_call(call_id: str) -> ToolResponse:
    """
    Delete a call activity.
    
    Args:
        call_id: The ID of the call to delete
    """
    
    client = get_close_client()
    
    await client.delete(f"/activity/call/{call_id}/")
    
    return {"success": True, "callId": call_id}


async def search_calls(
    query: str,
    limit: Optional[int] = None,
    **kwargs
) -> ToolResponse:
    """
    Search for calls in Close CRM.
    
    Args:
        query: Search query string
        limit: Maximum number of results to return (1-200, default 25)
    """
    
    client = get_close_client()
    
    params = remove_none_values({
        "query": query,
        "_limit": min(limit, CLOSE_MAX_LIMIT) if limit else 25,
    })
    
    response = await client.get("/activity/call/", params=params)
    
    return {
        "calls": [normalize_call_activity(c) for c in response.get("data", [])],
        "hasMore": response.get("has_more", False),
        "totalCount": response.get("total_results"),
    }
