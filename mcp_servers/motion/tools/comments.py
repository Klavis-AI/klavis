import logging
from typing import Any, Dict
from .base import make_api_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_comments(task_id: str) -> Dict[str, Any]:
    """Get comments for a specific task."""
    logger.info(f"Executing tool: get_comments for task_id={task_id}")
    try:
        endpoint = f"/tasks/{task_id}/comments"
        return await make_api_request(endpoint)
    except Exception as e:
        logger.exception(f"Error executing tool get_comments: {e}")
        raise e

async def create_comment(task_id: str, content: str) -> Dict[str, Any]:
    """Create a comment on a task."""
    logger.info(f"Executing tool: create_comment for task_id={task_id}")
    try:
        data = {
            "content": content
        }
        endpoint = f"/tasks/{task_id}/comments"
        return await make_api_request(endpoint, method="POST", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool create_comment: {e}")
        raise e 