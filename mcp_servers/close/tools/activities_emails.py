import logging
from typing import Any, List, Optional

from .base import (
    CloseToolExecutionError,
    ToolResponse,
    get_close_client,
    remove_none_values,
    normalize_email_activity,
)
from .constants import CLOSE_MAX_LIMIT

logger = logging.getLogger(__name__)


async def list_emails(
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
    List email activities from Close CRM.
    
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
    
    response = await client.get("/activity/email/", params=params)
    
    return {
        "emails": [normalize_email_activity(e) for e in response.get("data", [])],
        "hasMore": response.get("has_more", False),
        "totalCount": response.get("total_results"),
    }


async def get_email(email_id: str) -> ToolResponse:
    """
    Get a specific email activity by ID.
    
    Args:
        email_id: The ID of the email to retrieve
    """
    
    client = get_close_client()
    
    response = await client.get(f"/activity/email/{email_id}/")
    
    return {"email": normalize_email_activity(response)}


async def create_email(
    lead_id: str,
    subject: str,
    body_text: Optional[str] = None,
    body_html: Optional[str] = None,
    to: Optional[List[str]] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    sender: Optional[str] = None,
    status: Optional[str] = None,
    template_id: Optional[str] = None,
    **kwargs
) -> ToolResponse:
    """
    Create a new email activity in Close CRM.
    
    Args:
        lead_id: The ID of the lead this email belongs to
        subject: Email subject line
        body_text: Plain text version of email body
        body_html: HTML version of email body
        to: List of recipient email addresses
        cc: List of CC email addresses
        bcc: List of BCC email addresses
        sender: Sender email address
        status: Email status ('draft', 'scheduled', 'outbox', 'sent', etc.)
        template_id: Email template ID to use
    """
    
    client = get_close_client()
    
    email_data = remove_none_values({
        "lead_id": lead_id,
        "subject": subject,
        "body_text": body_text,
        "body_html": body_html,
        "to": to,
        "cc": cc,
        "bcc": bcc,
        "sender": sender,
        "status": status,
        "template_id": template_id,
    })
    
    if not body_text and not body_html:
        raise CloseToolExecutionError("Either body_text or body_html must be provided")
    
    response = await client.post("/activity/email/", json_data=email_data)
    
    return {"email": normalize_email_activity(response)}


async def update_email(
    email_id: str,
    subject: Optional[str] = None,
    body_text: Optional[str] = None,
    body_html: Optional[str] = None,
    to: Optional[List[str]] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    status: Optional[str] = None,
    **kwargs
) -> ToolResponse:
    """
    Update an existing email activity.
    
    Args:
        email_id: The ID of the email to update
        subject: Email subject line
        body_text: Plain text version of email body
        body_html: HTML version of email body
        to: List of recipient email addresses
        cc: List of CC email addresses
        bcc: List of BCC email addresses
        status: Email status
    """
    
    client = get_close_client()
    
    email_data = remove_none_values({
        "subject": subject,
        "body_text": body_text,
        "body_html": body_html,
        "to": to,
        "cc": cc,
        "bcc": bcc,
        "status": status,
    })
    
    if not email_data:
        raise CloseToolExecutionError("No update data provided")
    
    response = await client.put(f"/activity/email/{email_id}/", json_data=email_data)
    
    return {"email": normalize_email_activity(response)}


async def delete_email(email_id: str) -> ToolResponse:
    """
    Delete an email activity.
    
    Args:
        email_id: The ID of the email to delete
    """
    
    client = get_close_client()
    
    await client.delete(f"/activity/email/{email_id}/")
    
    return {"success": True, "emailId": email_id}


async def send_email(
    email_id: str,
    **kwargs
) -> ToolResponse:
    """
    Send a draft email.
    
    Args:
        email_id: The ID of the draft email to send
    """
    
    client = get_close_client()
    
    response = await client.post(f"/activity/email/{email_id}/send/", json_data={})
    
    return {"email": normalize_email_activity(response)}


async def search_emails(
    query: str,
    limit: Optional[int] = None,
    **kwargs
) -> ToolResponse:
    """
    Search for emails in Close CRM.
    
    Args:
        query: Search query string
        limit: Maximum number of results to return (1-200, default 25)
    """
    
    client = get_close_client()
    
    params = remove_none_values({
        "query": query,
        "_limit": min(limit, CLOSE_MAX_LIMIT) if limit else 25,
    })
    
    response = await client.get("/activity/email/", params=params)
    
    return {
        "emails": [normalize_email_activity(e) for e in response.get("data", [])],
        "hasMore": response.get("has_more", False),
        "totalCount": response.get("total_results"),
    }

