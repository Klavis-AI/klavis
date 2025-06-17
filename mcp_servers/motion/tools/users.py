import logging
from typing import Any, Dict, Optional
from .base import make_api_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_users(workspace_id: Optional[str] = None) -> Dict[str, Any]:
    """Get all users."""
    logger.info("Executing tool: get_users")
    try:
        endpoint = "/users"
        if workspace_id:
            endpoint += f"?workspaceId={workspace_id}"
            
        return await make_api_request(endpoint)
    except Exception as e:
        logger.exception(f"Error executing tool get_users: {e}")
        raise e

async def get_my_user() -> Dict[str, Any]:
    """Get current user information."""
    logger.info("Executing tool: get_my_user")
    try:
        endpoint = "/users/me"
        return await make_api_request(endpoint)
    except Exception as e:
        logger.exception(f"Error executing tool get_my_user: {e}")
        raise e 