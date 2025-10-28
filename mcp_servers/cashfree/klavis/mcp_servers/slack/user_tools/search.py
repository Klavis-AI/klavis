import logging
from typing import Any, Dict, Optional, List
from .base import make_slack_user_request

# Configure logging
logger = logging.getLogger(__name__)

# user_search_messages searches for messages in the workspace using user token (includes private channels and DMs)
# User tokens: search:read
async def user_search_messages(
    query: str,
    channel_ids: Optional[List[str]] = None,
    sort: Optional[str] = None,
    sort_dir: Optional[str] = None,
    count: Optional[int] = None,
    cursor: Optional[str] = None,
    highlight: Optional[bool] = None
) -> Dict[str, Any]:
    """Search for messages in the workspace using user token (includes private channels and DMs)."""
    logger.info(f"Executing tool: user_search_messages with query: {query}")
    
    # Construct the query with channel filters if provided
    search_query = query
    if channel_ids and len(channel_ids) > 0:
        # Add channel filters to the query
        channels_filter = " ".join([f"in:{channel_id}" for channel_id in channel_ids])
        search_query = f"{query} {channels_filter}"
    
    params = {
        "query": search_query,
    }
    
    if count:
        params["count"] = str(min(count, 100))
    else:
        params["count"] = "20"
    
    if highlight is not None:
        params["highlight"] = "1" if highlight else "0"
    else:
        params["highlight"] = "1"
    
    if sort:
        params["sort"] = sort
    else:
        params["sort"] = "score"
    
    if sort_dir:
        params["sort_dir"] = sort_dir
    else:
        params["sort_dir"] = "desc"
    
    if cursor:
        params["cursor"] = cursor
    
    try:
        return await make_slack_user_request("GET", "search.messages", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool user_search_messages: {e}")
        raise e
