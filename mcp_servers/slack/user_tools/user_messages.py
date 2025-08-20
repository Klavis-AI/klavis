import logging
from typing import Any, Dict, Optional
from .base import make_slack_user_request

# Configure logging
logger = logging.getLogger(__name__)

# Sends a message to a channel as a user
# User tokens: chat:write, chat:write:user, chat:write:bot
async def user_post_message(
    channel_id: str,
    text: str
) -> Dict[str, Any]:
    """Post a new message to a Slack channel using user token."""
    logger.info(f"Executing tool: user_post_message to channel {channel_id}")
    
    data = {
        "channel": channel_id,
        "text": text
    }
    
    try:
        return await make_slack_user_request("POST", "chat.postMessage", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool user_post_message: {e}")
        raise e

# Replies to a thread in a channel as a user
# User tokens: chat:write, chat:write:user, chat:write:bot
async def user_reply_to_thread(
    channel_id: str,
    thread_ts: str,
    text: str
) -> Dict[str, Any]:
    """Reply to a specific message thread in Slack using user token."""
    logger.info(f"Executing tool: user_reply_to_thread in channel {channel_id}, thread {thread_ts}")
    
    data = {
        "channel": channel_id,
        "thread_ts": thread_ts,
        "text": text
    }
    
    try:
        return await make_slack_user_request("POST", "chat.postMessage", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool user_reply_to_thread: {e}")
        raise e

# Adds a reaction to a message as a user
# User tokens: reactions:write
async def user_add_reaction(
    channel_id: str,
    timestamp: str,
    reaction: str
) -> Dict[str, Any]:
    """Add a reaction emoji to a message using user token."""
    logger.info(f"Executing tool: user_add_reaction to message {timestamp} in channel {channel_id}")
    
    data = {
        "channel": channel_id,
        "timestamp": timestamp,
        "name": reaction
    }
    
    try:
        return await make_slack_user_request("POST", "reactions.add", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool user_add_reaction: {e}")
        raise e
