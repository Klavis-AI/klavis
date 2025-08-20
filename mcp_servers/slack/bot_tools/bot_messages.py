import logging
from typing import Any, Dict, Optional
from .base import make_slack_bot_request

# Configure logging
logger = logging.getLogger(__name__)

# Sends a message to a channel as a bot
# Bot tokens: chat:write
async def bot_post_message(
    channel_id: str,
    text: str
) -> Dict[str, Any]:
    """Post a new message to a Slack channel using bot token."""
    logger.info(f"Executing tool: bot_post_message to channel {channel_id}")
    
    data = {
        "channel": channel_id,
        "text": text
    }
    
    try:
        return await make_slack_bot_request("POST", "chat.postMessage", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool bot_post_message: {e}")
        raise e

# Replies to a thread in a channel as a bot
# Bot tokens: chat:write
async def bot_reply_to_thread(
    channel_id: str,
    thread_ts: str,
    text: str
) -> Dict[str, Any]:
    """Reply to a specific message thread in Slack using bot token."""
    logger.info(f"Executing tool: bot_reply_to_thread in channel {channel_id}, thread {thread_ts}")
    
    data = {
        "channel": channel_id,
        "thread_ts": thread_ts,
        "text": text
    }
    
    try:
        return await make_slack_bot_request("POST", "chat.postMessage", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool bot_reply_to_thread: {e}")
        raise e

# Adds a reaction to a message as a bot
# Bot tokens: reactions:write
async def bot_add_reaction(
    channel_id: str,
    timestamp: str,
    reaction: str
) -> Dict[str, Any]:
    """Add a reaction emoji to a message using bot token."""
    logger.info(f"Executing tool: bot_add_reaction to message {timestamp} in channel {channel_id}")
    
    data = {
        "channel": channel_id,
        "timestamp": timestamp,
        "name": reaction
    }
    
    try:
        return await make_slack_bot_request("POST", "reactions.add", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool bot_add_reaction: {e}")
        raise e
