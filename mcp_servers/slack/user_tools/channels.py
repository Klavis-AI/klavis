import logging
from typing import Any, Dict, Optional
from .base import make_slack_user_request

# Configure logging
logger = logging.getLogger(__name__)

# list_channels returns all channels that the user has access to
# User tokens: channels:read, groups:read, im:read, mpim:read
async def list_channels(
    limit: Optional[int] = None,
    cursor: Optional[str] = None,
    types: Optional[str] = None
) -> Dict[str, Any]:
    """List channels in the workspace with pagination."""
    logger.info("Executing tool: slack_list_channels")
    
    params = {
        "exclude_archived": "true",
    }
    
    if limit:
        params["limit"] = str(min(limit, 200))
    else:
        params["limit"] = "100"
    
    if cursor:
        params["cursor"] = cursor
    
    if types:
        params["types"] = types
    else:
        params["types"] = "public_channel"
    
    try:
        return await make_slack_user_request("GET", "conversations.list", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool slack_list_channels: {e}")
        raise e
