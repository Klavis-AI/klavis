import logging
from typing import Any, Dict, Optional, List
from .base import make_slack_user_request

# Configure logging
logger = logging.getLogger(__name__)


async def get_current_user_id() -> str:
    """Get the user ID of the authenticated user using auth.test.

    This API does not require any additional scopes for user tokens.

    Returns:
        The user ID of the authenticated user.

    Raises:
        Exception: If the auth.test API call fails.
    """
    response = await make_slack_user_request("GET", "auth.test")
    if not response.get("ok"):
        error = response.get("error", "Unknown error")
        raise Exception(f"Failed to get current user info: {error}")
    return response.get("user_id")


def format_message_response(
    match: dict[str, Any],
    response_format: str = "concise",
) -> dict[str, Any]:
    """Format a single message match based on response_format.

    Args:
        match: Raw message match object from Slack API
        response_format: "concise" or "detailed"

    Returns:
        Formatted message object
    """
    if response_format == "detailed":
        return match

    channel = match.get("channel", {})

    formatted: dict[str, Any] = {
        "channel_id": channel.get("id"),
        "channel_name": channel.get("name"),  # None for DMs
        "user_id": match.get("user"),
        "username": match.get("username"),
        "ts": match.get("ts"),
        "text": match.get("text"),
        "permalink": match.get("permalink"),
    }

    # Add thread_ts if this is a threaded message
    if match.get("thread_ts"):
        formatted["thread_ts"] = match.get("thread_ts")

    return formatted


def generate_summary(
    total: int,
    returned: int,
    has_more: bool,
    include_hint: bool = True,
) -> str:
    """Generate summary string for the response.

    Args:
        total: Total number of messages found
        returned: Number of messages returned in this response
        has_more: Whether there are more results available
        include_hint: Whether to include hint for getting full message details

    Returns:
        Summary string
    """
    parts = [f"Found {total} messages"]

    if total > returned:
        parts.append(f"showing {returned}")

    summary = ", ".join(parts) + "."

    if has_more:
        summary += " Use next_cursor for more results."

    if include_hint:
        summary += (
            " To get full message details, use slack_get_channel_history with "
            "channel_id and latest=ts, inclusive=true, limit=1. "
            "For threaded messages, use slack_get_thread_replies."
        )

    return summary


# User tokens: search:read
async def user_search_messages(
    query: str,
    channel_ids: Optional[List[str]] = None,
    to_me: bool = False,
    sort: Optional[str] = None,
    sort_dir: Optional[str] = None,
    count: Optional[int] = None,
    cursor: Optional[str] = None,
    highlight: Optional[bool] = None,
    response_format: Optional[str] = None
) -> Dict[str, Any]:
    """Search for messages in the workspace using user token (includes private channels and DMs)."""
    logger.info(f"Executing tool: user_search_messages with query: {query}")

    # Build the search query
    search_query = query

    # Add to_me filter if requested
    if to_me:
        user_id = await get_current_user_id()
        search_query = f"{search_query} to:<@{user_id}>"

    # Add channel filters if provided
    if channel_ids and len(channel_ids) > 0:
        # Add channel filters to the query
        channels_filter = " ".join([f"in:{channel_id}" for channel_id in channel_ids])
        search_query = f"{search_query} {channels_filter}"

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

    if response_format is None:
        response_format = "concise"

    try:
        response = await make_slack_user_request("GET", "search.messages", params=params)

        if not response.get("ok", False):
            return response

        messages = response.get("messages", {})
        matches = messages.get("matches", [])
        total = messages.get("total", 0)

        # Format matches based on response_format
        formatted_matches = [
            format_message_response(match, response_format) for match in matches
        ]

        # Check for pagination
        response_metadata = response.get("response_metadata", {})
        next_cursor = response_metadata.get("next_cursor", "")
        has_more = bool(next_cursor)

        # Generate summary (include hint only for concise format)
        include_hint = response_format == "concise"
        summary = generate_summary(total, len(formatted_matches), has_more, include_hint)

        result = {
            "ok": True,
            "query": search_query,
            "messages": {
                "total": total,
                "matches": formatted_matches,
            },
            "summary": summary,
        }

        if response_metadata:
            result["response_metadata"] = response_metadata

        return result

    except Exception as e:
        logger.exception(f"Error executing tool user_search_messages: {e}")
        raise e
