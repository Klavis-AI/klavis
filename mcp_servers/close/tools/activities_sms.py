import logging
from typing import Any, List, Optional

from .base import (
    CloseToolExecutionError,
    ToolResponse,
    get_close_client,
    remove_none_values,
)
from .constants import CLOSE_MAX_LIMIT

logger = logging.getLogger(__name__)


async def list_sms(
    limit: Optional[int] = None,
    skip: Optional[int] = None,
    lead_id: Optional[str] = None,
    contact_id: Optional[str] = None,
    user_id: Optional[str] = None,
    direction: Optional[str] = None,
    date_created__gte: Optional[str] = None,
    date_created__lte: Optional[str] = None,
    **kwargs
) -> ToolResponse:
    """
    List SMS activities from Close CRM.
    
    Args:
        limit: Maximum number of results to return (1-200, default 100)
        skip: Number of results to skip for pagination
        lead_id: Filter by lead ID
        contact_id: Filter by contact ID
        user_id: Filter by user ID
        direction: Filter by direction ('incoming' or 'outgoing')
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
        "date_created__gte": date_created__gte,
        "date_created__lte": date_created__lte,
    })
    
    response = await client.get("/activity/sms/", params=params)
    
    return {
        "sms": response.get("data", []),
        "has_more": response.get("has_more", False),
        "total_results": response.get("total_results"),
    }


async def get_sms(sms_id: str) -> ToolResponse:
    """
    Get a specific SMS activity by ID.
    
    Args:
        sms_id: The ID of the SMS to retrieve
    """
    
    client = get_close_client()
    
    response = await client.get(f"/activity/sms/{sms_id}/")
    
    return response


async def create_sms(
    lead_id: str,
    text: str,
    direction: str,
    remote_phone: Optional[str] = None,
    local_phone: Optional[str] = None,
    contact_id: Optional[str] = None,
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    date_created: Optional[str] = None,
    **kwargs
) -> ToolResponse:
    """
    Create a new SMS activity in Close CRM.
    
    Args:
        lead_id: The ID of the lead this SMS belongs to
        text: SMS message text
        direction: SMS direction ('incoming' or 'outgoing')
        remote_phone: Remote phone number (recipient for outgoing, sender for incoming)
        local_phone: Local phone number (your number)
        contact_id: The ID of the contact
        user_id: The ID of the user who sent/received the SMS
        status: SMS status ('draft', 'scheduled', 'sent', 'delivered', 'failed', etc.)
        date_created: Date the SMS was created (ISO 8601 format)
    """
    
    client = get_close_client()
    
    sms_data = remove_none_values({
        "lead_id": lead_id,
        "text": text,
        "direction": direction,
        "remote_phone": remote_phone,
        "local_phone": local_phone,
        "contact_id": contact_id,
        "user_id": user_id,
        "status": status,
        "date_created": date_created,
    })
    
    if direction not in ["incoming", "outgoing"]:
        raise CloseToolExecutionError("Direction must be 'incoming' or 'outgoing'")
    
    response = await client.post("/activity/sms/", json_data=sms_data)
    
    return response


async def update_sms(
    sms_id: str,
    text: Optional[str] = None,
    status: Optional[str] = None,
    remote_phone: Optional[str] = None,
    local_phone: Optional[str] = None,
    **kwargs
) -> ToolResponse:
    """
    Update an existing SMS activity.
    
    Args:
        sms_id: The ID of the SMS to update
        text: SMS message text
        status: SMS status
        remote_phone: Remote phone number
        local_phone: Local phone number
    """
    
    client = get_close_client()
    
    sms_data = remove_none_values({
        "text": text,
        "status": status,
        "remote_phone": remote_phone,
        "local_phone": local_phone,
    })
    
    if not sms_data:
        raise CloseToolExecutionError("No update data provided")
    
    response = await client.put(f"/activity/sms/{sms_id}/", json_data=sms_data)
    
    return response


async def delete_sms(sms_id: str) -> ToolResponse:
    """
    Delete an SMS activity.
    
    Args:
        sms_id: The ID of the SMS to delete
    """
    
    client = get_close_client()
    
    response = await client.delete(f"/activity/sms/{sms_id}/")
    
    return {"success": True, "sms_id": sms_id}


async def send_sms(
    sms_id: str,
    **kwargs
) -> ToolResponse:
    """
    Send a draft SMS.
    
    Args:
        sms_id: The ID of the draft SMS to send
    """
    
    client = get_close_client()
    
    response = await client.post(f"/activity/sms/{sms_id}/send/", json_data={})
    
    return response


async def search_sms(
    query: str,
    limit: Optional[int] = None,
    **kwargs
) -> ToolResponse:
    """
    Search for SMS messages in Close CRM.
    
    Args:
        query: Search query string
        limit: Maximum number of results to return (1-200, default 25)
    """
    
    client = get_close_client()
    
    params = remove_none_values({
        "query": query,
        "_limit": min(limit, CLOSE_MAX_LIMIT) if limit else 25,
    })
    
    response = await client.get("/activity/sms/", params=params)
    
    return {
        "sms": response.get("data", []),
        "has_more": response.get("has_more", False),
        "total_results": response.get("total_results"),
    }

