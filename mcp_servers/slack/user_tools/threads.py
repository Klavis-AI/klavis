import logging
from typing import Any, Dict, Optional
from .base import make_slack_user_request, format_reactions

logger = logging.getLogger(__name__)


def format_thread_message(
    message: dict[str, Any],
    thread_ts: str,
    response_format: str = "concise",
) -> dict[str, Any]:
    """Format a single thread message based on response_format.

    Args:
        message: Raw message object from Slack API
        thread_ts: The thread timestamp to determine if message is parent
        response_format: "concise" or "detailed"

    Returns:
        Formatted message object
    """
    if response_format == "detailed":
        return message

    ts = message.get("ts")
    is_parent = ts == thread_ts

    formatted: dict[str, Any] = {
        "user_id": message.get("user"),
        "ts": ts,
        "text": message.get("text"),
        "thread_ts": message.get("thread_ts"),
        "is_parent": is_parent,
    }

    if is_parent:
        formatted["reply_count"] = message.get("reply_count", 0)
    else:
        formatted["parent_user_id"] = message.get("parent_user_id")

    # Add reactions if present
    reactions = message.get("reactions")
    if reactions:
        formatted["reactions"] = format_reactions(reactions)

    return formatted


def generate_thread_summary(
    returned: int,
    has_more: bool,
) -> str:
    """Generate summary string for thread response.

    Args:
        returned: Number of messages returned
        has_more: Whether there are more messages available

    Returns:
        Summary string
    """
    summary = f"Found {returned} messages in thread."

    if has_more:
        summary += " Use next_cursor for more results."

    return summary


# get_thread_replies returns all replies in a message thread
# User tokens: channels:history, groups:history, im:history, mpim:history
async def get_thread_replies(
    channel_id: str,
    thread_ts: str,
    limit: Optional[int] = None,
    cursor: Optional[str] = None,
    oldest: Optional[str] = None,
    latest: Optional[str] = None,
    inclusive: Optional[bool] = None,
    response_format: Optional[str] = None
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
        response_format: "concise" (default) or "detailed"

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

    if response_format is None:
        response_format = "concise"

    try:
        response = await make_slack_user_request("GET", "conversations.replies", params=params)

        if not response.get("ok", False):
            return response

        messages = response.get("messages", [])
        has_more = response.get("has_more", False)

        # Format messages based on response_format
        formatted_messages = [
            format_thread_message(msg, thread_ts, response_format) for msg in messages
        ]

        result = {
            "ok": True,
            "messages": formatted_messages,
            "has_more": has_more,
            "summary": generate_thread_summary(len(formatted_messages), has_more),
        }

        response_metadata = response.get("response_metadata", {})
        if response_metadata:
            result["response_metadata"] = response_metadata

        return result

    except Exception as e:
        logger.exception(f"Error executing tool get_thread_replies: {e}")
        raise e

