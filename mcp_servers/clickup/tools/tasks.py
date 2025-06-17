import logging
from typing import Any, Dict, Optional, List
from .base import make_clickup_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_tasks(
    list_id: str,
    archived: bool = False,
    include_closed: bool = False,
    page: int = 0,
    order_by: str = "created",
    reverse: bool = False,
    subtasks: bool = False,
    statuses: Optional[List[str]] = None,
    include_markdown_description: bool = False,
    assignees: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    due_date_gt: Optional[int] = None,
    due_date_lt: Optional[int] = None,
    date_created_gt: Optional[int] = None,
    date_created_lt: Optional[int] = None,
    date_updated_gt: Optional[int] = None,
    date_updated_lt: Optional[int] = None
) -> Dict[str, Any]:
    """Get tasks from a list with optional filtering."""
    logger.info(f"Executing tool: get_tasks with list_id: {list_id}")
    try:
        params = {
            "archived": str(archived).lower(),
            "include_closed": str(include_closed).lower(),
            "page": page,
            "order_by": order_by,
            "reverse": str(reverse).lower(),
            "subtasks": str(subtasks).lower(),
            "include_markdown_description": str(include_markdown_description).lower()
        }
        
        if statuses:
            params["statuses[]"] = statuses
        if assignees:
            params["assignees[]"] = assignees
        if tags:
            params["tags[]"] = tags
        if due_date_gt:
            params["due_date_gt"] = due_date_gt
        if due_date_lt:
            params["due_date_lt"] = due_date_lt
        if date_created_gt:
            params["date_created_gt"] = date_created_gt
        if date_created_lt:
            params["date_created_lt"] = date_created_lt
        if date_updated_gt:
            params["date_updated_gt"] = date_updated_gt
        if date_updated_lt:
            params["date_updated_lt"] = date_updated_lt
            
        result = await make_clickup_request(f"list/{list_id}/task", params=params)
        return result
    except Exception as e:
        logger.exception(f"Error executing tool get_tasks: {e}")
        raise e

async def get_task_by_id(task_id: str, custom_task_ids: bool = False, team_id: Optional[str] = None, include_subtasks: bool = False) -> Dict[str, Any]:
    """Get a specific task by ID."""
    logger.info(f"Executing tool: get_task_by_id with task_id: {task_id}")
    try:
        params = {
            "custom_task_ids": str(custom_task_ids).lower(),
            "include_subtasks": str(include_subtasks).lower()
        }
        if team_id:
            params["team_id"] = team_id
            
        result = await make_clickup_request(f"task/{task_id}", params=params)
        return result
    except Exception as e:
        logger.exception(f"Error executing tool get_task_by_id: {e}")
        raise e

async def create_task(
    list_id: str,
    name: str,
    description: Optional[str] = None,
    assignees: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    status: Optional[str] = None,
    priority: Optional[int] = None,
    due_date: Optional[int] = None,
    due_date_time: bool = False,
    time_estimate: Optional[int] = None,
    start_date: Optional[int] = None,
    start_date_time: bool = False,
    notify_all: bool = True,
    parent: Optional[str] = None,
    links_to: Optional[str] = None,
    check_required_custom_fields: bool = True,
    custom_task_ids: bool = False,
    team_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new task."""
    logger.info(f"Executing tool: create_task with name: {name}")
    try:
        data = {"name": name}
        
        if description:
            data["description"] = description
        if assignees:
            data["assignees"] = assignees
        if tags:
            data["tags"] = tags
        if status:
            data["status"] = status
        if priority:
            data["priority"] = priority
        if due_date:
            data["due_date"] = due_date
        if due_date_time:
            data["due_date_time"] = due_date_time
        if time_estimate:
            data["time_estimate"] = time_estimate
        if start_date:
            data["start_date"] = start_date
        if start_date_time:
            data["start_date_time"] = start_date_time
        if notify_all is not None:
            data["notify_all"] = notify_all
        if parent:
            data["parent"] = parent
        if links_to:
            data["links_to"] = links_to
        if check_required_custom_fields is not None:
            data["check_required_custom_fields"] = check_required_custom_fields
            
        params = {
            "custom_task_ids": str(custom_task_ids).lower()
        }
        if team_id:
            params["team_id"] = team_id
            
        result = await make_clickup_request(f"list/{list_id}/task", "POST", data, params)
        return result
    except Exception as e:
        logger.exception(f"Error executing tool create_task: {e}")
        raise e

async def update_task(
    task_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[int] = None,
    due_date: Optional[int] = None,
    due_date_time: Optional[bool] = None,
    parent: Optional[str] = None,
    time_estimate: Optional[int] = None,
    start_date: Optional[int] = None,
    start_date_time: Optional[bool] = None,
    assignees: Optional[Dict[str, Any]] = None,
    archived: Optional[bool] = None,
    custom_task_ids: bool = False,
    team_id: Optional[str] = None
) -> Dict[str, Any]:
    """Update an existing task."""
    logger.info(f"Executing tool: update_task with task_id: {task_id}")
    try:
        data = {}
        
        if name:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if status:
            data["status"] = status
        if priority is not None:
            data["priority"] = priority
        if due_date is not None:
            data["due_date"] = due_date
        if due_date_time is not None:
            data["due_date_time"] = due_date_time
        if parent:
            data["parent"] = parent
        if time_estimate is not None:
            data["time_estimate"] = time_estimate
        if start_date is not None:
            data["start_date"] = start_date
        if start_date_time is not None:
            data["start_date_time"] = start_date_time
        if assignees:
            data["assignees"] = assignees
        if archived is not None:
            data["archived"] = archived
            
        params = {
            "custom_task_ids": str(custom_task_ids).lower()
        }
        if team_id:
            params["team_id"] = team_id
            
        result = await make_clickup_request(f"task/{task_id}", "PUT", data, params)
        return result
    except Exception as e:
        logger.exception(f"Error executing tool update_task: {e}")
        raise e

async def search_tasks(
    team_id: str,
    query: str,
    start: int = 0,
    limit: int = 20
) -> Dict[str, Any]:
    """Search for tasks by text query."""
    logger.info(f"Executing tool: search_tasks with query: {query}")
    try:
        params = {
            "query": query,
            "start": start,
            "limit": limit
        }
        
        result = await make_clickup_request(f"team/{team_id}/task", params=params)
        return result
    except Exception as e:
        logger.exception(f"Error executing tool search_tasks: {e}")
        raise e 