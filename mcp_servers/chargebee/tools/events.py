import logging
from typing import Any, Dict, Optional
from .base import make_request

# Configure logging
logger = logging.getLogger(__name__)


async def list_events(
    limit: Optional[int] = None,
    offset: Optional[str] = None,
    event_type: Optional[str] = None,
    occurred_at_after: Optional[int] = None,
    occurred_at_before: Optional[int] = None,
) -> Dict[str, Any]:
    """List all events from Chargebee with optional filters."""
    logger.info("Executing tool: list_events")

    params = {}

    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    if event_type is not None:
        params["event_type[is]"] = event_type
    if occurred_at_after is not None:
        params["occurred_at[after]"] = occurred_at_after
    if occurred_at_before is not None:
        params["occurred_at[before]"] = occurred_at_before

    try:
        return await make_request("GET", "/events", params=params if params else None)
    except Exception as e:
        logger.exception(f"Error executing tool list_events: {e}")
        raise e


async def get_event(event_id: str) -> Dict[str, Any]:
    """Get detailed information for a specific event from Chargebee."""
    logger.info(f"Executing tool: get_event for event_id={event_id}")

    try:
        return await make_request("GET", f"/events/{event_id}")
    except Exception as e:
        logger.exception(f"Error executing tool get_event: {e}")
        raise e
