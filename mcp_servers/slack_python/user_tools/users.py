import logging
from typing import Any, Dict, Optional
from .base import make_slack_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_users(
    cursor: Optional[str] = None,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """Get a list of all users in the workspace with their basic profile information."""
    logger.info("Executing tool: slack_get_users")
    
    params = {}
    
    if limit:
        params["limit"] = str(min(limit, 200))
    else:
        params["limit"] = "100"
    
    if cursor:
        params["cursor"] = cursor
    
    # Add team_id if available from environment
    import os
    team_id = os.getenv("SLACK_TEAM_ID")
    if team_id:
        params["team_id"] = team_id
    
    try:
        return await make_slack_request("GET", "users.list", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool slack_get_users: {e}")
        raise e

async def get_user_profile(
    user_id: str
) -> Dict[str, Any]:
    """Get detailed profile information for a specific user."""
    logger.info(f"Executing tool: slack_get_user_profile for user {user_id}")
    
    params = {
        "user": user_id,
        "include_labels": "true"
    }
    
    try:
        return await make_slack_request("GET", "users.profile.get", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool slack_get_user_profile: {e}")
        raise e
