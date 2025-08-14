import logging
from typing import Any, Dict, Optional

from .base import get_freshdesk_client, FreshdeskToolExecutionError
from .create_ticket import validate_priority, validate_status, validate_email

logger = logging.getLogger(__name__)


async def update_ticket(
    ticket_id: int,
    subject: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[int] = None,
    status: Optional[int] = None,
    cc_emails: Optional[list[str]] = None,
    tags: Optional[list[str]] = None,
) -> Dict[str, Any]:
    # Input validation
    if not ticket_id or ticket_id <= 0:
        raise FreshdeskToolExecutionError(
            "Valid ticket ID is required",
            f"Invalid ticket ID: {ticket_id}"
        )
    
    # Validate that at least one field is provided for update
    update_fields = [subject, description, priority, status, cc_emails, tags]
    if all(field is None for field in update_fields):
        raise FreshdeskToolExecutionError(
            "At least one field must be provided for update",
            "No update fields provided"
        )
    
    # Validate individual fields
    if subject is not None and not subject.strip():
        raise FreshdeskToolExecutionError(
            "Subject cannot be empty if provided",
            "Empty subject provided"
        )
    
    if priority is not None:
        validate_priority(priority)
    
    if status is not None:
        validate_status(status)
    
    # Validate CC emails if provided
    if cc_emails:
        for cc_email in cc_emails:
            validate_email(cc_email)
    
    client = get_freshdesk_client()
    payload: Dict[str, Any] = {}
    
    if subject is not None:
        payload["subject"] = subject.strip()
    if description is not None:
        payload["description"] = description.strip() if description else ""
    if priority is not None:
        payload["priority"] = priority
    if status is not None:
        payload["status"] = status
    if cc_emails is not None:
        payload["cc_emails"] = [email.strip() for email in cc_emails if email.strip()]
    if tags is not None:
        payload["tags"] = [tag.strip() for tag in tags if tag.strip()]

    try:
        result = await client.put(f"/tickets/{ticket_id}", json_data=payload)
        logger.info(f"Successfully updated ticket {ticket_id}")
        return result
    except Exception as e:
        logger.error(f"Failed to update ticket {ticket_id}: {str(e)}")
        raise
