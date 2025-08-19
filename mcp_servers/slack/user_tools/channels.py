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
    """List all channels the authenticated user has access to.
    
    This uses the user token to list channels, which means it can access:
    - Public channels in the workspace
    - Private channels the user is a member of
    - Direct messages (DMs)
    - Multi-party direct messages (group DMs)
    
    Args:
        limit: Maximum number of channels to return (default 100, max 200)
        cursor: Pagination cursor for next page of results
        types: Channel types to include (public_channel, private_channel, mpim, im)
    
    Returns:
        Dictionary containing the list of channels and pagination metadata
    """
    logger.info("Executing tool: slack_user_list_channels")
    
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
        logger.exception(f"Error executing tool slack_user_list_channels: {e}")
        raise e

# get_channel_history returns the most recent messages from a channel
# User tokens: channels:history, groups:history, im:history, mpim:history
async def get_channel_history(
    channel_id: str,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """Get recent messages from a channel."""
    logger.info(f"Executing tool: slack_get_channel_history for channel {channel_id}")
    
    params = {
        "channel": channel_id,
    }
    
    if limit:
        params["limit"] = str(limit)
    else:
        params["limit"] = "10"
    
    try:
        return await make_slack_user_request("GET", "conversations.history", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool slack_get_channel_history: {e}")
        raise e
