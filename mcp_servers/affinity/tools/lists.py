import logging
from typing import Any, Dict, Optional
from .base import make_http_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_lists() -> Dict[str, Any]:
    """Get all lists in the Affinity workspace."""
    logger.info("Executing tool: get_lists")
    try:
        return await make_http_request("GET", "/lists")
    except Exception as e:
        logger.exception(f"Error executing tool get_lists: {e}")
        raise e

async def get_list_by_id(list_id: int) -> Dict[str, Any]:
    """Get a specific list by ID."""
    logger.info(f"Executing tool: get_list_by_id with list_id: {list_id}")
    try:
        return await make_http_request("GET", f"/lists/{list_id}")
    except Exception as e:
        logger.exception(f"Error executing tool get_list_by_id: {e}")
        raise e

async def create_list(name: str, list_type: int = 0) -> Dict[str, Any]:
    """Create a new list."""
    logger.info(f"Executing tool: create_list with name: {name}")
    try:
        data = {
            "name": name,
            "type": list_type
        }
        return await make_http_request("POST", "/lists", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool create_list: {e}")
        raise e 