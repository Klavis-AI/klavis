import logging
from typing import Any, Dict, Optional
from .base import make_clickup_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_lists(folder_id: Optional[str] = None, space_id: Optional[str] = None) -> Dict[str, Any]:
    """Get all lists in a folder or space."""
    logger.info(f"Executing tool: get_lists with folder_id: {folder_id}, space_id: {space_id}")
    try:
        if folder_id:
            result = await make_clickup_request(f"folder/{folder_id}/list")
        elif space_id:
            result = await make_clickup_request(f"space/{space_id}/list")
        else:
            raise ValueError("Either folder_id or space_id must be provided")
        return result
    except Exception as e:
        logger.exception(f"Error executing tool get_lists: {e}")
        raise e

async def create_list(
    folder_id: Optional[str] = None, 
    space_id: Optional[str] = None,
    name: str = None, 
    content: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: Optional[int] = None,
    assignee: Optional[str] = None,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new list in a folder or space."""
    logger.info(f"Executing tool: create_list with name: {name}")
    try:
        data = {"name": name}
        if content:
            data["content"] = content
        if due_date:
            data["due_date"] = due_date
        if priority:
            data["priority"] = priority
        if assignee:
            data["assignee"] = assignee
        if status:
            data["status"] = status
            
        if folder_id:
            result = await make_clickup_request(f"folder/{folder_id}/list", "POST", data)
        elif space_id:
            result = await make_clickup_request(f"space/{space_id}/list", "POST", data)
        else:
            raise ValueError("Either folder_id or space_id must be provided")
        return result
    except Exception as e:
        logger.exception(f"Error executing tool create_list: {e}")
        raise e

async def update_list(
    list_id: str, 
    name: Optional[str] = None, 
    content: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: Optional[int] = None,
    assignee: Optional[str] = None,
    unset_status: bool = False
) -> Dict[str, Any]:
    """Update an existing list."""
    logger.info(f"Executing tool: update_list with list_id: {list_id}")
    try:
        data = {}
        if name:
            data["name"] = name
        if content:
            data["content"] = content
        if due_date:
            data["due_date"] = due_date
        if priority:
            data["priority"] = priority
        if assignee:
            data["assignee"] = assignee
        if unset_status:
            data["unset_status"] = unset_status
            
        result = await make_clickup_request(f"list/{list_id}", "PUT", data)
        return result
    except Exception as e:
        logger.exception(f"Error executing tool update_list: {e}")
        raise e 