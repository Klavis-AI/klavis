import logging
from typing import Any, Dict, Optional

from .base import get_freshdesk_client, FreshdeskToolExecutionError

logger = logging.getLogger(__name__)


def validate_pagination_params(per_page: Optional[int], page: Optional[int]) -> None:
    """Validate pagination parameters."""
    if per_page is not None and (per_page < 1 or per_page > 100):
        raise FreshdeskToolExecutionError(
            "per_page must be between 1 and 100",
            f"Invalid per_page value: {per_page}"
        )
    
    if page is not None and page < 1:
        raise FreshdeskToolExecutionError(
            "page must be greater than 0",
            f"Invalid page value: {page}"
        )


def validate_order_type(order_type: Optional[str]) -> None:
    """Validate order type parameter."""
    valid_order_types = ["asc", "desc"]
    if order_type is not None and order_type not in valid_order_types:
        raise FreshdeskToolExecutionError(
            "order_type must be 'asc' or 'desc'",
            f"Invalid order_type: {order_type}"
        )


async def list_tickets(
    email: Optional[str] = None,
    updated_since: Optional[str] = None,
    per_page: Optional[int] = None,
    page: Optional[int] = None,
    order_type: Optional[str] = None,
) -> Dict[str, Any]:
    # Input validation
    validate_pagination_params(per_page, page)
    validate_order_type(order_type)
    
    # Validate email format if provided
    if email and ("@" not in email or "." not in email.split("@")[1]):
        raise FreshdeskToolExecutionError(
            "Invalid email format",
            f"Email validation failed for: {email}"
        )
    
    # Validate updated_since format if provided (basic ISO format check)
    if updated_since and not updated_since.replace("-", "").replace(":", "").replace("T", "").replace("Z", "").replace(".", "").isdigit():
        raise FreshdeskToolExecutionError(
            "updated_since must be in ISO format (e.g., '2023-01-01T00:00:00Z')",
            f"Invalid updated_since format: {updated_since}"
        )
    
    client = get_freshdesk_client()
    params: Dict[str, Any] = {}
    
    if email:
        params["email"] = email.strip()
    if updated_since:
        params["updated_since"] = updated_since
    if per_page:
        params["per_page"] = per_page
    if page:
        params["page"] = page
    if order_type:
        params["order_type"] = order_type
    
    try:
        result = await client.get("/tickets", params=params)
        logger.info(f"Successfully listed tickets with {len(result.get('tickets', []))} results")
        return result
    except Exception as e:
        logger.error(f"Failed to list tickets: {str(e)}")
        raise
