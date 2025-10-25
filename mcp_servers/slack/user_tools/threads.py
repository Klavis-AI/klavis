import logging
from typing import Any, Dict, Optional
from .base import make_slack_user_request

logger = logging.getLogger(__name__)

# get_thread_replies returns all replies in a message thread
# User tokens: channels:history, groups:history, im:history, mpim:history
async def get_thread_replies(
    channel_id: str,
    thread_ts: str,
    limit: Optional[int] = None,
    cursor: Optional[str] = None,
    oldest: Optional[str] = None,
    latest: Optional[str] = None,
    inclusive: Optional[bool] = None
) -> Dict[str, Any]:
    """Get all replies in a message thread.
    
    This retrieves all messages in a thread, including the parent message.
    Works with public channels, private channels, DMs, and group DMs that
    the authenticated user has access to.
    
    Args:
        channel_id: The ID of the channel containing the thread (e.g., 'C1234567890')
        thread_ts: The timestamp of the parent message that started the thread (e.g., '1234567890.123456')
        limit: Maximum number of messages to return (default 10, max 1000)
        cursor: Pagination cursor for next page of results
        oldest: Only messages after this Unix timestamp (inclusive)
        latest: Only messages before this Unix timestamp (exclusive)
        inclusive: Include messages with oldest or latest timestamps in results
    
    Returns:
        Dictionary containing:
        - messages: List of messages in the thread (includes parent as first message)
        - has_more: Boolean indicating if there are more messages
        - response_metadata: Contains cursor for pagination if has_more is True
    
    Examples:
        # Get a thread from a Slack URL like:
        # https://workspace.slack.com/archives/C123456/p1234567890123456
        # Parse to: channel_id='C123456', thread_ts='1234567890.123456'
        
        result = await get_thread_replies(
            channel_id='C123456',
            thread_ts='1234567890.123456',
            limit=50
        )
    """
    logger.info(f"Executing tool: get_thread_replies for channel {channel_id}, thread {thread_ts}")
    
    params = {
        "channel": channel_id,
        "ts": thread_ts,
    }
    
    if limit:
        params["limit"] = str(min(limit, 1000))
    else:
        params["limit"] = "10"
    
    if cursor:
        params["cursor"] = cursor
    
    if oldest:
        params["oldest"] = oldest
    
    if latest:
        params["latest"] = latest
    
    if inclusive is not None:
        params["inclusive"] = "true" if inclusive else "false"
    
    try:
        return await make_slack_user_request("GET", "conversations.replies", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool get_thread_replies: {e}")
        raise e

