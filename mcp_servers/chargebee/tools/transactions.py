import logging
from typing import Any, Dict, Optional
from .base import make_request

# Configure logging
logger = logging.getLogger(__name__)


async def list_transactions(
    limit: Optional[int] = None,
    offset: Optional[str] = None,
    customer_id: Optional[str] = None,
    subscription_id: Optional[str] = None,
    payment_source_id: Optional[str] = None,
    payment_method: Optional[str] = None,
    status: Optional[str] = None,
    date_after: Optional[int] = None,
    date_before: Optional[int] = None,
) -> Dict[str, Any]:
    """List all transactions from Chargebee with optional filters."""
    logger.info("Executing tool: list_transactions")

    params = {}

    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    if customer_id is not None:
        params["customer_id[is]"] = customer_id
    if subscription_id is not None:
        params["subscription_id[is]"] = subscription_id
    if payment_source_id is not None:
        params["payment_source_id[is]"] = payment_source_id
    if payment_method is not None:
        params["payment_method[is]"] = payment_method
    if status is not None:
        params["status[is]"] = status
    if date_after is not None:
        params["date[after]"] = date_after
    if date_before is not None:
        params["date[before]"] = date_before

    try:
        return await make_request("GET", "/transactions", params=params if params else None)
    except Exception as e:
        logger.exception(f"Error executing tool list_transactions: {e}")
        raise e
