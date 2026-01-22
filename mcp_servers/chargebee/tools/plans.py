import logging
from typing import Any, Dict, Optional
from .base import make_request

# Configure logging
logger = logging.getLogger(__name__)


async def list_items(
    limit: Optional[int] = None,
    offset: Optional[str] = None,
    status: Optional[str] = None,
    item_type: Optional[str] = None,
) -> Dict[str, Any]:
    """List all items (plans, addons, charges) from Chargebee Product Catalog 2.0."""
    logger.info("Executing tool: list_items")

    params = {}

    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    if status is not None:
        params["status[is]"] = status
    if item_type is not None:
        params["type[is]"] = item_type

    try:
        return await make_request("GET", "/items", params=params if params else None)
    except Exception as e:
        logger.exception(f"Error executing tool list_items: {e}")
        raise e


async def get_item(item_id: str) -> Dict[str, Any]:
    """Get detailed information for a specific item from Chargebee Product Catalog 2.0."""
    logger.info(f"Executing tool: get_item for item_id={item_id}")

    try:
        return await make_request("GET", f"/items/{item_id}")
    except Exception as e:
        logger.exception(f"Error executing tool get_item: {e}")
        raise e


