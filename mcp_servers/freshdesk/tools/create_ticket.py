import logging
from typing import Any, Dict, Optional

from .base import get_freshdesk_client, FreshdeskToolExecutionError

logger = logging.getLogger(__name__)


def validate_priority(priority: Optional[int]) -> None:
    """Validate ticket priority value."""
    if priority is not None and (priority < 1 or priority > 4):
        raise FreshdeskToolExecutionError(
            "Priority must be between 1 and 4 (1=Low, 2=Medium, 3=High, 4=Urgent)",
            f"Invalid priority value: {priority}"
        )


def validate_status(status: Optional[int]) -> None:
    """Validate ticket status value."""
    valid_statuses = {2, 3, 4, 5}  # Open, Pending, Resolved, Closed
    if status is not None and status not in valid_statuses:
        raise FreshdeskToolExecutionError(
            "Status must be one of: 2=Open, 3=Pending, 4=Resolved, 5=Closed",
            f"Invalid status value: {status}"
        )


def validate_email(email: str) -> None:
    """Basic email validation."""
    if not email or "@" not in email or "." not in email.split("@")[1]:
        raise FreshdeskToolExecutionError(
            "Invalid email format",
            f"Email validation failed for: {email}"
        )


async def create_ticket(
    subject: str,
    email: str,
    description: Optional[str] = None,
    priority: Optional[int] = None,
    status: Optional[int] = None,
    cc_emails: Optional[list[str]] = None,
    tags: Optional[list[str]] = None,
) -> Dict[str, Any]:
    # Input validation
    if not subject or not subject.strip():
        raise FreshdeskToolExecutionError(
            "Subject is required and cannot be empty",
            "Empty or missing subject"
        )
    
    validate_email(email)
    validate_priority(priority)
    validate_status(status)
    
    # Validate CC emails if provided
    if cc_emails:
        for cc_email in cc_emails:
            validate_email(cc_email)
    
    client = get_freshdesk_client()
    payload: Dict[str, Any] = {
        "subject": subject.strip(),
        "email": email.strip(),
    }
    
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
        result = await client.post("/tickets", json_data=payload)
        logger.info(f"Successfully created ticket with ID: {result.get('id')}")
        return result
    except Exception as e:
        logger.error(f"Failed to create ticket: {str(e)}")
        raise
