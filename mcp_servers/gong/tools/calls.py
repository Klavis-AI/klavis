import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, List

from .base import get, post

logger = logging.getLogger(__name__)

async def list_calls(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 50,
) -> Dict[str, Any]:
    """List calls in Gong between two datetimes (inclusive).

    If dates are not provided, defaults to the last 30 days.
    """
    if not from_date:
        from_date = (
            datetime.now(timezone.utc) - timedelta(days=30)
        ).isoformat(timespec="seconds")
    if not to_date:
        to_date = datetime.now(timezone.utc).isoformat(timespec="seconds")

    params = {
        "fromDateTime": from_date,
        "toDateTime": to_date,
        "limit": limit,
    }
    logger.info("Listing calls from %s to %s (limit=%s)", from_date, to_date, limit)
    return await get("/v2/calls", params=params)

async def add_new_call(call_data: Dict[str, Any]) -> Dict[str, Any]:
    """Add a new call record to Gong.

    The required structure of `call_data` is documented in the Gong API. At a minimum,
    you typically need start/end timestamps, parties, and a downloadMediaUrl.
    """
    if not call_data:
        raise ValueError("call_data cannot be empty")

    logger.info("Adding new call to Gong")
    return await post("/v2/calls", call_data) 