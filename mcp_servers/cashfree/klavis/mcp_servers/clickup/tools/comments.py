import logging
from typing import Any, Dict, Optional
from .base import make_clickup_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_comments(task_id: str, custom_task_ids: bool = False, team_id: Optional[str] = None) -> Dict[str, Any]:
    """Get comments for a specific task."""
    logger.info(f"Executing tool: get_comments with task_id: {task_id}")
    try:
        params = {
            "custom_task_ids": str(custom_task_ids).lower()
        }
        if team_id:
            params["team_id"] = team_id
            
        result = await make_clickup_request(f"task/{task_id}/comment", params=params)
        return result
    except Exception as e:
        logger.exception(f"Error executing tool get_comments: {e}")
        raise e

async def create_comment(
    task_id: str,
    comment_text: str,
    assignee: Optional[str] = None,
    notify_all: bool = True,
    custom_task_ids: bool = False,
    team_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create a comment on a task."""
    logger.info(f"Executing tool: create_comment on task: {task_id}")
    try:
        data = {
            "comment_text": comment_text,
            "notify_all": notify_all
        }
        if assignee:
            data["assignee"] = assignee
            
        params = {
            "custom_task_ids": str(custom_task_ids).lower()
        }
        if team_id:
            params["team_id"] = team_id
            
        result = await make_clickup_request(f"task/{task_id}/comment", "POST", data, params)
        return result
    except Exception as e:
        logger.exception(f"Error executing tool create_comment: {e}")
        raise e

async def update_comment(
    comment_id: str,
    comment_text: str,
    assignee: Optional[str] = None,
    resolved: Optional[bool] = None
) -> Dict[str, Any]:
    """Update an existing comment."""
    logger.info(f"Executing tool: update_comment with comment_id: {comment_id}")
    try:
        data = {"comment_text": comment_text}
        
        if assignee:
            data["assignee"] = assignee
        if resolved is not None:
            data["resolved"] = resolved
            
        result = await make_clickup_request(f"comment/{comment_id}", "PUT", data)
        return result
    except Exception as e:
        logger.exception(f"Error executing tool update_comment: {e}")
        raise e 