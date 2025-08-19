import logging
from typing import Any, Dict, Optional, List
from .base import make_slack_request

# Configure logging
logger = logging.getLogger(__name__)

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
    
    # Add team_id if available from environment
    import os
    team_id = os.getenv("SLACK_TEAM_ID")
    if team_id:
        params["team_id"] = team_id
    
    try:
        return await make_slack_request("GET", "conversations.list", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool slack_list_channels: {e}")
        raise e

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
        return await make_slack_request("GET", "conversations.history", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool slack_get_channel_history: {e}")
        raise e
