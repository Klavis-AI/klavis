import logging
from typing import Any, Dict, Optional
from .base import make_slack_bot_request

# Configure logging
logger = logging.getLogger(__name__)

async def post_message(
    channel_id: str,
    text: str
) -> Dict[str, Any]:
    """Post a new message to a Slack channel."""
    logger.info(f"Executing tool: slack_post_message to channel {channel_id}")
    
    data = {
        "channel": channel_id,
        "text": text
    }
    
    try:
        return await make_slack_bot_request("POST", "chat.postMessage", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool slack_post_message: {e}")
        raise e

async def reply_to_thread(
    channel_id: str,
    thread_ts: str,
    text: str
) -> Dict[str, Any]:
    """Reply to a specific message thread in Slack."""
    logger.info(f"Executing tool: slack_reply_to_thread in channel {channel_id}, thread {thread_ts}")
    
    data = {
        "channel": channel_id,
        "thread_ts": thread_ts,
        "text": text
    }
    
    try:
        return await make_slack_bot_request("POST", "chat.postMessage", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool slack_reply_to_thread: {e}")
        raise e

async def add_reaction(
    channel_id: str,
    timestamp: str,
    reaction: str
) -> Dict[str, Any]:
    """Add a reaction emoji to a message."""
    logger.info(f"Executing tool: slack_add_reaction to message {timestamp} in channel {channel_id}")
    
    data = {
        "channel": channel_id,
        "timestamp": timestamp,
        "name": reaction
    }
    
    try:
        return await make_slack_bot_request("POST", "reactions.add", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool slack_add_reaction: {e}")
        raise e

async def get_thread_replies(
    channel_id: str,
    thread_ts: str
) -> Dict[str, Any]:
    """Get all replies in a message thread."""
    logger.info(f"Executing tool: slack_get_thread_replies for thread {thread_ts} in channel {channel_id}")
    
    params = {
        "channel": channel_id,
        "ts": thread_ts
    }
    
    try:
        return await make_slack_bot_request("GET", "conversations.replies", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool slack_get_thread_replies: {e}")
        raise e
