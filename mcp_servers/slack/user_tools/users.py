import logging
from typing import Any, Dict, Optional
from .base import make_slack_user_request

# Configure logging
logger = logging.getLogger(__name__)

# Lists all users in a Slack team.
# User tokens: users:read
async def list_users(
    cursor: Optional[str] = None,
    limit: Optional[int] = None,
    team_id: Optional[str] = None,
    include_locale: Optional[bool] = None
) -> Dict[str, Any]:
    """Lists all users in a Slack team using users.list API."""
    logger.info("Executing tool: list_users")
    
    params = {}
    
    # Set limit (max 200 per page according to Slack API)
    if limit:
        params["limit"] = str(min(limit, 200))
    else:
        params["limit"] = "100"
    
    # Add cursor for pagination
    if cursor:
        params["cursor"] = cursor
    
    # Add team_id if provided (for Enterprise Grid)
    if team_id:
        params["team_id"] = team_id
    
    # Include locale information
    if include_locale is not None:
        params["include_locale"] = str(include_locale).lower()
    
    try:
        return await make_slack_user_request("GET", "users.list", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool list_users: {e}")
        raise e

# Gets information about a user.
# User tokens: users:read
async def user_get_info(
    user_id: str,
    include_locale: Optional[bool] = None
) -> Dict[str, Any]:
    """Gets information about a user using users.info API."""
    logger.info(f"Executing tool: user_get_info for user {user_id}")
    
    params = {
        "user": user_id
    }
    
    # Include locale information
    if include_locale is not None:
        params["include_locale"] = str(include_locale).lower()
    
    try:
        return await make_slack_user_request("GET", "users.info", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool user_get_info: {e}")
        raise e
