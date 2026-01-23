import logging
from typing import Any, Dict, Optional
from .base import make_request

# Configure logging
logger = logging.getLogger(__name__)


async def list_invoices(
    limit: Optional[int] = None,
    offset: Optional[str] = None,
    customer_id: Optional[str] = None,
    subscription_id: Optional[str] = None,
    status: Optional[str] = None,
    paid_at_after: Optional[int] = None,
    paid_at_before: Optional[int] = None,
) -> Dict[str, Any]:
    """List all invoices from Chargebee with optional filters."""
    logger.info("Executing tool: list_invoices")

    params = {}

    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    if customer_id is not None:
        params["customer_id[is]"] = customer_id
    if subscription_id is not None:
        params["subscription_id[is]"] = subscription_id
    if status is not None:
        params["status[is]"] = status
    if paid_at_after is not None:
        params["paid_at[after]"] = paid_at_after
    if paid_at_before is not None:
        params["paid_at[before]"] = paid_at_before

    try:
        return await make_request("GET", "/invoices", params=params if params else None)
    except Exception as e:
        logger.exception(f"Error executing tool list_invoices: {e}")
        raise e


async def get_invoice(invoice_id: str) -> Dict[str, Any]:
    """Get detailed information for a specific invoice from Chargebee."""
    logger.info(f"Executing tool: get_invoice for invoice_id={invoice_id}")

    try:
        return await make_request("GET", f"/invoices/{invoice_id}")
    except Exception as e:
        logger.exception(f"Error executing tool get_invoice: {e}")
        raise e
