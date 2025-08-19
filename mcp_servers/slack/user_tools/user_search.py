import logging
from typing import Any, Dict, Optional, List
from .base import make_slack_user_request

# Configure logging
logger = logging.getLogger(__name__)

async def search_user_messages(
    query: str,
    sort: Optional[str] = None,
    sort_dir: Optional[str] = None,
    count: Optional[int] = None,
    cursor: Optional[str] = None
) -> Dict[str, Any]:
    """Search for messages using user permissions (includes private channels and DMs)."""
    logger.info(f"Executing tool: slack_user_search_messages with query: {query}")
    
    params = {
        "query": query,
    }
    
    if count:
        params["count"] = str(min(count, 100))
    else:
        params["count"] = "20"
    
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
    
    # Always highlight for user searches
    params["highlight"] = "1"
    
    try:
        return await make_slack_user_request("GET", "search.messages", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool slack_user_search_messages: {e}")
        raise e

async def search_user_files(
    query: str,
    count: Optional[int] = None,
    cursor: Optional[str] = None
) -> Dict[str, Any]:
    """Search for files using user permissions."""
    logger.info(f"Executing tool: slack_user_search_files with query: {query}")
    
    params = {
        "query": query,
    }
    
    if count:
        params["count"] = str(min(count, 100))
    else:
        params["count"] = "20"
    
    if cursor:
        params["cursor"] = cursor
    
    params["highlight"] = "1"
    
    try:
        return await make_slack_user_request("GET", "search.files", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool slack_user_search_files: {e}")
        raise e
