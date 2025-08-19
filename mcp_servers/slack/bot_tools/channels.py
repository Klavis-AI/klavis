import logging
from typing import Any, Dict, Optional
from .base import make_slack_bot_request

# Configure logging
logger = logging.getLogger(__name__)

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
        return await make_slack_bot_request("GET", "conversations.history", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool slack_get_channel_history: {e}")
        raise e
