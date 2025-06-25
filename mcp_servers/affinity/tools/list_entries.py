import logging
from typing import Any, Dict, Optional
from .base import make_http_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_list_entries(list_id: int, page_size: int = 10, page_token: Optional[str] = None) -> Dict[str, Any]:
    """Get list entries for a specific list."""
    logger.info(f"Executing tool: get_list_entries with list_id: {list_id}")
    try:
        params = {
            "list_id": list_id,
            "page_size": page_size
        }
        if page_token:
            params["page_token"] = page_token
        
        return await make_http_request("GET", "/list-entries", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool get_list_entries: {e}")
        raise e

async def get_list_entry_by_id(list_entry_id: int) -> Dict[str, Any]:
    """Get a specific list entry by ID."""
    logger.info(f"Executing tool: get_list_entry_by_id with list_entry_id: {list_entry_id}")
    try:
        return await make_http_request("GET", f"/list-entries/{list_entry_id}")
    except Exception as e:
        logger.exception(f"Error executing tool get_list_entry_by_id: {e}")
        raise e

async def create_list_entry(
    list_id: int, 
    entity_id: int, 
    creator_id: Optional[int] = None
) -> Dict[str, Any]:
    """Create a new list entry."""
    logger.info(f"Executing tool: create_list_entry with list_id: {list_id}, entity_id: {entity_id}")
    try:
        data = {
            "list_id": list_id,
            "entity_id": entity_id
        }
        if creator_id:
            data["creator_id"] = creator_id
        
        return await make_http_request("POST", "/list-entries", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool create_list_entry: {e}")
        raise e

async def delete_list_entry(list_entry_id: int) -> Dict[str, Any]:
    """Delete a specific list entry."""
    logger.info(f"Executing tool: delete_list_entry with list_entry_id: {list_entry_id}")
    try:
        return await make_http_request("DELETE", f"/list-entries/{list_entry_id}")
    except Exception as e:
        logger.exception(f"Error executing tool delete_list_entry: {e}")
        raise e 