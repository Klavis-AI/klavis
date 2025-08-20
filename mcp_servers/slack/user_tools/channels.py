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

# invite_users_to_channel invites users to a channel
# User tokens: channels:write.invites, groups:write.invites, im:write.invites, mpim:write.invites
async def invite_users_to_channel(
    channel_id: str,
    user_ids: list[str]
) -> Dict[str, Any]:
    """Invite one or more users (including bot users) to a channel.
    
    This uses the user token to invite users to a channel. The authenticated user must have
    permission to invite users to the specified channel. Both regular users and bot users
    can be invited using their respective user IDs.
    
    Args:
        channel_id: The ID of the channel to invite users to (e.g., 'C1234567890')
        user_ids: A list of user IDs to invite (e.g., ['U1234567890', 'U9876543210'])
    
    Returns:
        Dictionary containing the updated channel information
    """
    logger.info(f"Executing tool: slack_invite_users_to_channel for channel {channel_id}")
    
    if not user_ids:
        raise ValueError("At least one user ID must be provided")
    
    # Slack API expects comma-separated user IDs
    data = {
        "channel": channel_id,
        "users": ",".join(user_ids)
    }
    
    try:
        return await make_slack_user_request("POST", "conversations.invite", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool slack_invite_users_to_channel: {e}")
        raise e
