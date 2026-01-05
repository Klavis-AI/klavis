import logging
from typing import Any, List, Optional

from .base import (
    CloseToolExecutionError,
    ToolResponse,
    get_close_client,
    remove_none_values,
    normalize_whatsapp_activity,
)
from .constants import CLOSE_MAX_LIMIT

logger = logging.getLogger(__name__)


async def list_whatsapp(
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
    List WhatsApp message activities from Close CRM.
    
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
    
    response = await client.get("/activity/whatsapp_message/", params=params)
    
    return {
        "messages": [normalize_whatsapp_activity(m) for m in response.get("data", [])],
        "hasMore": response.get("has_more", False),
        "totalCount": response.get("total_results"),
    }


async def get_whatsapp(whatsapp_id: str) -> ToolResponse:
    """
    Get a specific WhatsApp message activity by ID.
    
    Args:
        whatsapp_id: The ID of the WhatsApp message to retrieve
    """
    
    client = get_close_client()
    
    response = await client.get(f"/activity/whatsapp_message/{whatsapp_id}/")
    
    return {"message": normalize_whatsapp_activity(response)}


async def create_whatsapp(
    lead_id: str,
    external_whatsapp_message_id: str,
    message_markdown: str,
    direction: Optional[str] = None,
    attachments: Optional[List[dict]] = None,
    integration_link: Optional[str] = None,
    response_to_id: Optional[str] = None,
    user_id: Optional[str] = None,
    contact_id: Optional[str] = None,
    date_created: Optional[str] = None,
    send_to_inbox: Optional[bool] = None,
    **kwargs
) -> ToolResponse:
    """
    Create a new WhatsApp message activity in Close CRM.
    
    Args:
        lead_id: The ID of the lead this WhatsApp message belongs to
        external_whatsapp_message_id: The ID of the message within WhatsApp
        message_markdown: The body of the message in WhatsApp Markdown format
        direction: Message direction ('incoming' or 'outgoing')
        attachments: List of attachment objects with url, filename, and content_type
                    Note: url must begin with https://app.close.com/go/file/
        integration_link: A URL linking back to the message in the external system
        response_to_id: The Close activity ID of another WhatsApp message this message is replying to
        user_id: The ID of the user who sent/received the message
        contact_id: The ID of the contact
        date_created: Date the message was created (ISO 8601 format)
        send_to_inbox: Create a corresponding Inbox Notification for incoming messages (query param)
    """
    
    client = get_close_client()
    
    whatsapp_data = remove_none_values({
        "lead_id": lead_id,
        "external_whatsapp_message_id": external_whatsapp_message_id,
        "message_markdown": message_markdown,
        "direction": direction,
        "attachments": attachments,
        "integration_link": integration_link,
        "response_to_id": response_to_id,
        "user_id": user_id,
        "contact_id": contact_id,
        "date_created": date_created,
    })
    
    # Validate direction if provided
    if direction and direction not in ["incoming", "outgoing"]:
        raise CloseToolExecutionError("Direction must be 'incoming' or 'outgoing'")
    
    # Validate attachments if provided
    if attachments:
        for attachment in attachments:
            if "url" not in attachment:
                raise CloseToolExecutionError("Each attachment must have a url")
            if not attachment["url"].startswith("https://app.close.com/go/file/"):
                raise CloseToolExecutionError("Attachment URL must begin with 'https://app.close.com/go/file/'")
    
    # Add send_to_inbox as query parameter if provided
    params = {}
    if send_to_inbox is not None:
        params["send_to_inbox"] = "true" if send_to_inbox else "false"
    
    response = await client.post("/activity/whatsapp_message/", json_data=whatsapp_data, params=params if params else None)
    
    return {"message": normalize_whatsapp_activity(response)}


async def update_whatsapp(
    whatsapp_id: str,
    message_markdown: Optional[str] = None,
    attachments: Optional[List[dict]] = None,
    integration_link: Optional[str] = None,
    **kwargs
) -> ToolResponse:
    """
    Update an existing WhatsApp message activity.
    
    Args:
        whatsapp_id: The ID of the WhatsApp message to update
        message_markdown: The body of the message in WhatsApp Markdown format
        attachments: List of attachment objects with url, filename, and content_type
        integration_link: A URL linking back to the message in the external system
    """
    
    client = get_close_client()
    
    whatsapp_data = remove_none_values({
        "message_markdown": message_markdown,
        "attachments": attachments,
        "integration_link": integration_link,
    })
    
    if not whatsapp_data:
        raise CloseToolExecutionError("No update data provided")
    
    # Validate attachments if provided
    if attachments:
        for attachment in attachments:
            if "url" not in attachment:
                raise CloseToolExecutionError("Each attachment must have a url")
            if not attachment["url"].startswith("https://app.close.com/go/file/"):
                raise CloseToolExecutionError("Attachment URL must begin with 'https://app.close.com/go/file/'")
    
    response = await client.put(f"/activity/whatsapp_message/{whatsapp_id}/", json_data=whatsapp_data)
    
    return {"message": normalize_whatsapp_activity(response)}


async def delete_whatsapp(whatsapp_id: str) -> ToolResponse:
    """
    Delete a WhatsApp message activity.
    
    Args:
        whatsapp_id: The ID of the WhatsApp message to delete
    """
    
    client = get_close_client()
    
    await client.delete(f"/activity/whatsapp_message/{whatsapp_id}/")
    
    return {"success": True, "messageId": whatsapp_id}


async def search_whatsapp(
    query: str,
    limit: Optional[int] = None,
    **kwargs
) -> ToolResponse:
    """
    Search for WhatsApp messages in Close CRM.
    
    Args:
        query: Search query string
        limit: Maximum number of results to return (1-200, default 25)
    """
    
    client = get_close_client()
    
    params = remove_none_values({
        "query": query,
        "_limit": min(limit, CLOSE_MAX_LIMIT) if limit else 25,
    })
    
    response = await client.get("/activity/whatsapp_message/", params=params)
    
    return {
        "messages": [normalize_whatsapp_activity(m) for m in response.get("data", [])],
        "hasMore": response.get("has_more", False),
        "totalCount": response.get("total_results"),
    }
