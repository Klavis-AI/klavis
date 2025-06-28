import logging
from typing import Any, Dict, Optional, List
from .base import make_v2_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_all_list_entries_on_a_list(
    list_id: int,
    cursor: Optional[str] = None,
    limit: Optional[int] = None,
    field_ids: Optional[List[str]] = None,
    field_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Get all List Entries on a List.
    
    Args:
        list_id: List ID
        cursor: Cursor for pagination
        limit: Number of items per page (1-100, default 100)
        field_ids: Field IDs for field data
        field_types: Field types (enriched, global, list, relationship-intelligence)
    """
    logger.info(f"Executing tool: get_all_list_entries_on_a_list with list_id: {list_id}")
    try:
        params = {}
        if cursor:
            params["cursor"] = cursor
        if limit:
            params["limit"] = limit
        if field_ids:
            params["fieldIds"] = field_ids
        if field_types:
            params["fieldTypes"] = field_types
            
        return await make_v2_request("GET", f"/lists/{list_id}/list-entries", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool get_all_list_entries_on_a_list: {e}")
        raise e

async def get_metadata_on_all_lists(
    cursor: Optional[str] = None,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """Get metadata on all Lists.
    
    Args:
        cursor: Cursor for pagination
        limit: Number of items per page (1-100, default 100)
    """
    logger.info("Executing tool: get_metadata_on_all_lists")
    try:
        params = {}
        if cursor:
            params["cursor"] = cursor
        if limit:
            params["limit"] = limit
            
        return await make_v2_request("GET", "/lists", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool get_metadata_on_all_lists: {e}")
        raise e

async def get_metadata_on_a_single_list(list_id: int) -> Dict[str, Any]:
    """Get metadata on a single List.
    
    Args:
        list_id: List ID
    """
    logger.info(f"Executing tool: get_metadata_on_a_single_list with list_id: {list_id}")
    try:
        return await make_v2_request("GET", f"/lists/{list_id}")
    except Exception as e:
        logger.exception(f"Error executing tool get_metadata_on_a_single_list: {e}")
        raise e

async def get_metadata_on_a_single_list_fields(
    list_id: int,
    cursor: Optional[str] = None,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """Get metadata on a single List's Fields.
    
    Args:
        list_id: List ID
        cursor: Cursor for pagination
        limit: Number of items per page (1-100, default 100)
    """
    logger.info(f"Executing tool: get_metadata_on_a_single_list_fields with list_id: {list_id}")
    try:
        params = {}
        if cursor:
            params["cursor"] = cursor
        if limit:
            params["limit"] = limit
            
        return await make_v2_request("GET", f"/lists/{list_id}/fields", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool get_metadata_on_a_single_list_fields: {e}")
        raise e

async def get_a_single_list_entry_on_a_list(
    list_id: int,
    list_entry_id: int,
    field_ids: Optional[List[str]] = None,
    field_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Get a single List Entry on a List.
    
    Args:
        list_id: List ID
        list_entry_id: List Entry ID
        field_ids: Field IDs for field data
        field_types: Field types (enriched, global, list, relationship-intelligence)
    """
    logger.info(f"Executing tool: get_a_single_list_entry_on_a_list with list_id: {list_id}, list_entry_id: {list_entry_id}")
    try:
        params = {}
        if field_ids:
            params["fieldIds"] = field_ids
        if field_types:
            params["fieldTypes"] = field_types
            
        return await make_v2_request("GET", f"/lists/{list_id}/list-entries/{list_entry_id}", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool get_a_single_list_entry_on_a_list: {e}")
        raise e