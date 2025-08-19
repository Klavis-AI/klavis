import logging
from typing import Any, Dict, Optional
from .base import make_slack_user_request

# Configure logging
logger = logging.getLogger(__name__)

async def open_direct_message(
    users: str  # Comma-separated list of user IDs
) -> Dict[str, Any]:
    """Open a direct message channel with one or more users."""
    logger.info(f"Executing tool: slack_user_open_dm with users: {users}")
    
    data = {
        "users": users
    }
    
    try:
        return await make_slack_user_request("POST", "conversations.open", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool slack_user_open_dm: {e}")
        raise e

async def post_direct_message(
    user_id: str,
    text: str
) -> Dict[str, Any]:
    """Post a direct message to a user."""
    logger.info(f"Executing tool: slack_user_post_dm to user {user_id}")
    
    # First, open a DM channel with the user
    dm_response = await open_direct_message(user_id)
    
    if not dm_response.get("ok"):
        raise Exception(f"Failed to open DM channel: {dm_response.get('error', 'Unknown error')}")
    
    channel_id = dm_response.get("channel", {}).get("id")
    if not channel_id:
        raise Exception("Failed to get DM channel ID")
    
    # Now post the message
    data = {
        "channel": channel_id,
        "text": text
    }
    
    try:
        return await make_slack_user_request("POST", "chat.postMessage", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool slack_user_post_dm: {e}")
        raise e

async def post_ephemeral_message(
    channel_id: str,
    user_id: str,
    text: str
) -> Dict[str, Any]:
    """Post an ephemeral message visible only to a specific user."""
    logger.info(f"Executing tool: slack_user_post_ephemeral to user {user_id} in channel {channel_id}")
    
    data = {
        "channel": channel_id,
        "user": user_id,
        "text": text
    }
    
    try:
        return await make_slack_user_request("POST", "chat.postEphemeral", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool slack_user_post_ephemeral: {e}")
        raise e
