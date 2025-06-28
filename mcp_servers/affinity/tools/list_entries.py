import logging
from typing import Any, Dict, Optional
from .base import make_http_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_list_entries(list_id: int, page_size: Optional[int] = None, page_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Get list entries for a specific list.
    
    Args:
        list_id: The unique ID of the list whose list entries are to be retrieved
        page_size: How many results to return per page (optional, defaults to all results if not specified)
        page_token: The next_page_token from the previous response required to retrieve the next page of results
    
    Returns:
        If page_size is not specified: Array of list entry resources
        If page_size is specified: Object with 'list_entries' array and 'next_page_token' string
    """
    logger.info(f"Executing tool: get_list_entries with list_id: {list_id}")
    try:
        params = {}
        if page_size is not None:
            params["page_size"] = page_size
        if page_token:
            params["page_token"] = page_token
        
        return await make_http_request("GET", f"/lists/{list_id}/list-entries", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool get_list_entries: {e}")
        raise e

async def get_list_entry_by_id(list_id: int, list_entry_id: int) -> Dict[str, Any]:
    """
    Get a specific list entry by ID.
    
    Args:
        list_id: The unique ID of the list that contains the specified list_entry_id
        list_entry_id: The unique ID of the list entry object to be retrieved
    
    Returns:
        The list entry object corresponding to the list_entry_id
    """
    logger.info(f"Executing tool: get_list_entry_by_id with list_id: {list_id}, list_entry_id: {list_entry_id}")
    try:
        return await make_http_request("GET", f"/lists/{list_id}/list-entries/{list_entry_id}")
    except Exception as e:
        logger.exception(f"Error executing tool get_list_entry_by_id: {e}")
        raise e

async def create_list_entry(
    list_id: int, 
    entity_id: int, 
    creator_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create a new list entry.
    
    Args:
        list_id: The unique ID of the list to add the entry to
        entity_id: The unique ID of the person or organization to add to this list
        creator_id: The ID of a Person resource who should be recorded as adding the entry to the list
    
    Returns:
        The list entry resource that was just created
    
    Notes:
        - Opportunities cannot be created using this endpoint. Use POST /opportunities instead.
        - Person and company lists can contain the same entity multiple times.
    """
    logger.info(f"Executing tool: create_list_entry with list_id: {list_id}, entity_id: {entity_id}")
    try:
        data = {
            "entity_id": entity_id
        }
        if creator_id:
            data["creator_id"] = creator_id
        
        return await make_http_request("POST", f"/lists/{list_id}/list-entries", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool create_list_entry: {e}")
        raise e

async def delete_list_entry(list_id: int, list_entry_id: int) -> Dict[str, Any]:
    """
    Delete a specific list entry.
    
    Args:
        list_id: The unique ID of the list that contains the specified list_entry_id
        list_entry_id: The unique ID of the list entry object to be deleted
    
    Returns:
        JSON object {"success": true}
    
    Notes:
        - This will also delete all field values associated with the list entry
        - If the list entry belongs to an Opportunity list, the opportunity will also be deleted
    """
    logger.info(f"Executing tool: delete_list_entry with list_id: {list_id}, list_entry_id: {list_entry_id}")
    try:
        return await make_http_request("DELETE", f"/lists/{list_id}/list-entries/{list_entry_id}")
    except Exception as e:
        logger.exception(f"Error executing tool delete_list_entry: {e}")
        raise e 