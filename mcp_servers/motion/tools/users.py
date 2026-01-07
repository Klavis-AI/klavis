import logging
from typing import Any, Dict, Optional
from .base import make_api_request
from .normalize import normalize_user, normalize_users

# Configure logging
logger = logging.getLogger(__name__)

async def get_users(workspace_id: Optional[str] = None) -> Dict[str, Any]:
    """Get all users."""
    logger.info("Executing tool: get_users")
    try:
        endpoint = "/users"
        if workspace_id:
            endpoint += f"?workspaceId={workspace_id}"
            
        raw_response = await make_api_request(endpoint)
        users = normalize_users(raw_response.get("users", []))
        return {
            "count": len(users),
            "users": users,
        }
    except Exception as e:
        logger.exception(f"Error executing tool get_users: {e}")
        raise e

async def get_my_user() -> Dict[str, Any]:
    """Get current user information."""
    logger.info("Executing tool: get_my_user")
    try:
        endpoint = "/users/me"
        raw_response = await make_api_request(endpoint)
        return normalize_user(raw_response)
    except Exception as e:
        logger.exception(f"Error executing tool get_my_user: {e}")
        raise e 