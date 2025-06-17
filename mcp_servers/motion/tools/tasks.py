import logging
from typing import Any, Dict, Optional
from .base import make_api_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_tasks(workspace_id: Optional[str] = None) -> Dict[str, Any]:
    """Get all tasks."""
    logger.info("Executing tool: get_tasks")
    try:
        endpoint = "/tasks"
        params = {}
        if workspace_id:
            params["workspaceId"] = workspace_id
            
        if params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            endpoint += f"?{query_string}"
            
        return await make_api_request(endpoint)
    except Exception as e:
        logger.exception(f"Error executing tool get_tasks: {e}")
        raise e

async def get_task(task_id: str) -> Dict[str, Any]:
    """Get a specific task by ID."""
    logger.info(f"Executing tool: get_task with task_id={task_id}")
    try:
        endpoint = f"/tasks/{task_id}"
        return await make_api_request(endpoint)
    except Exception as e:
        logger.exception(f"Error executing tool get_task: {e}")
        raise e

async def create_task(
    name: str,
    workspace_id: str,
    description: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assignee_id: Optional[str] = None,
    project_id: Optional[str] = None,
    due_date: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new task."""
    logger.info(f"Executing tool: create_task with name={name}")
    try:
        data = {
            "name": name,
            "workspaceId": workspace_id
        }
        
        if description:
            data["description"] = description
        if status:
            data["status"] = status
        if priority:
            data["priority"] = priority
        if assignee_id:
            data["assigneeId"] = assignee_id
        if project_id:
            data["projectId"] = project_id
        if due_date:
            data["dueDate"] = due_date
            
        return await make_api_request("/tasks", method="POST", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool create_task: {e}")
        raise e

async def update_task(
    task_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assignee_id: Optional[str] = None,
    project_id: Optional[str] = None,
    due_date: Optional[str] = None
) -> Dict[str, Any]:
    """Update an existing task."""
    logger.info(f"Executing tool: update_task with task_id={task_id}")
    try:
        data = {}
        
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if status is not None:
            data["status"] = status
        if priority is not None:
            data["priority"] = priority
        if assignee_id is not None:
            data["assigneeId"] = assignee_id
        if project_id is not None:
            data["projectId"] = project_id
        if due_date is not None:
            data["dueDate"] = due_date
            
        return await make_api_request(f"/tasks/{task_id}", method="PATCH", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool update_task: {e}")
        raise e

async def delete_task(task_id: str) -> Dict[str, Any]:
    """Delete a task."""
    logger.info(f"Executing tool: delete_task with task_id={task_id}")
    try:
        await make_api_request(f"/tasks/{task_id}", method="DELETE")
        return {"success": True, "message": f"Task {task_id} deleted successfully"}
    except Exception as e:
        logger.exception(f"Error executing tool delete_task: {e}")
        raise e

async def search_tasks(query: str, workspace_id: Optional[str] = None) -> Dict[str, Any]:
    """Search tasks by name or description."""
    logger.info(f"Executing tool: search_tasks with query={query}")
    try:
        endpoint = f"/tasks?search={query}"
        if workspace_id:
            endpoint += f"&workspaceId={workspace_id}"
            
        return await make_api_request(endpoint)
    except Exception as e:
        logger.exception(f"Error executing tool search_tasks: {e}")
        raise e

 