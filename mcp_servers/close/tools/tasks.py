import logging
from typing import Any, Dict, List, Optional

from .base import (
    CloseToolExecutionError,
    ToolResponse,
    get_close_client,
    remove_none_values,
)
from .constants import CLOSE_MAX_LIMIT, TaskType

logger = logging.getLogger(__name__)


async def list_tasks(
    limit: Optional[int] = None,
    skip: Optional[int] = None,
    lead_id: Optional[str] = None,
    assigned_to: Optional[str] = None,
    is_complete: Optional[bool] = None,
    task_type: Optional[str] = None,
    view: Optional[str] = None,
    **kwargs
) -> ToolResponse:
    """List tasks from Close CRM."""
    
    client = get_close_client()
    
    params = remove_none_values({
        "_limit": min(limit, CLOSE_MAX_LIMIT) if limit else 100,
        "_skip": skip,
        "lead_id": lead_id,
        "assigned_to": assigned_to,
        "is_complete": is_complete,
        "_type": task_type,
        "view": view,
    })
    
    response = await client.get("/task/", params=params)
    
    return {
        "tasks": response.get("data", []),
        "has_more": response.get("has_more", False),
        "total_results": response.get("total_results"),
    }


async def get_task(task_id: str) -> ToolResponse:
    """Get a specific task by ID."""
    
    client = get_close_client()
    
    response = await client.get(f"/task/{task_id}/")
    
    return response


async def create_task(
    lead_id: str,
    text: str,
    assigned_to: Optional[str] = None,
    date: Optional[str] = None,
    is_complete: Optional[bool] = None,
    **kwargs
) -> ToolResponse:
    """Create a new task in Close CRM."""
    
    client = get_close_client()
    
    task_data = remove_none_values({
        "lead_id": lead_id,
        "text": text,
        "assigned_to": assigned_to,
        "date": date,
        "is_complete": is_complete or False,
    })
    
    response = await client.post("/task/", json_data=task_data)
    
    return response


async def update_task(
    task_id: str,
    text: Optional[str] = None,
    assigned_to: Optional[str] = None,
    date: Optional[str] = None,
    is_complete: Optional[bool] = None,
    **kwargs
) -> ToolResponse:
    """Update an existing task."""
    
    client = get_close_client()
    
    task_data = remove_none_values({
        "text": text,
        "assigned_to": assigned_to,
        "date": date,
        "is_complete": is_complete,
    })
    
    if not task_data:
        raise CloseToolExecutionError("No update data provided")
    
    response = await client.put(f"/task/{task_id}/", json_data=task_data)
    
    return response


async def delete_task(task_id: str) -> ToolResponse:
    """Delete a task."""
    
    client = get_close_client()
    
    response = await client.delete(f"/task/{task_id}/")
    
    return {"success": True, "task_id": task_id}


async def bulk_update_tasks(
    task_ids: List[str],
    assigned_to: Optional[str] = None,
    date: Optional[str] = None,
    is_complete: Optional[bool] = None,
    **kwargs
) -> ToolResponse:
    """Bulk update multiple tasks."""
    
    client = get_close_client()
    
    task_data = remove_none_values({
        "assigned_to": assigned_to,
        "date": date,
        "is_complete": is_complete,
    })
    
    if not task_data:
        raise CloseToolExecutionError("No update data provided")
    
    # Use the id__in filter for bulk operations
    params = {
        "id__in": ",".join(task_ids)
    }
    
    response = await client.put("/task/", params=params, json_data=task_data)
    
    return response


async def search_tasks(
    query: str,
    limit: Optional[int] = None,
    task_type: Optional[str] = None,
    **kwargs
) -> ToolResponse:
    """Search for tasks using Close CRM search."""
    
    client = get_close_client()
    
    params = remove_none_values({
        "query": query,
        "_limit": min(limit, CLOSE_MAX_LIMIT) if limit else 25,
        "_type": task_type,
    })
    
    response = await client.get("/task/", params=params)
    
    return {
        "tasks": response.get("data", []),
        "has_more": response.get("has_more", False),
        "total_results": response.get("total_results"),
    } 