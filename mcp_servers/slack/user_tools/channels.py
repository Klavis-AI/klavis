import logging
from typing import Any

from .base import make_slack_user_request

logger = logging.getLogger(__name__)


def filter_channels(
    channels: list[dict[str, Any]],
    channel_name: str | None = None,
    user_id: str | None = None,
) -> list[dict[str, Any]]:
    """Client-side filtering of channels.

    Args:
        channels: Raw channel list from Slack API
        channel_name: Optional channel name filter (case-insensitive partial match)
        user_id: Optional user ID filter for DMs (exact match)

    Returns:
        Filtered list of channels
    """
    if not channel_name and not user_id:
        return channels

    filtered = []

    if channel_name:
        channel_name_lower = channel_name.lower()
        filtered.extend(
            ch
            for ch in channels
            if not ch.get("is_im", False)
            and (
                channel_name_lower in ch.get("name", "").lower()
                or channel_name_lower in ch.get("name_normalized", "").lower()
            )
        )

    if user_id:
        filtered.extend(
            ch
            for ch in channels
            if ch.get("is_im", False) and ch.get("user") == user_id
        )

    return filtered


def format_channel_response(
    channel: dict[str, Any],
    response_format: str = "concise",
) -> dict[str, Any]:
    """Format a single channel object based on response_format.

    Args:
        channel: Raw channel object from Slack API
        response_format: "concise" or "detailed"

    Returns:
        Formatted channel object
    """
    if response_format == "detailed":
        return channel

    if channel.get("is_im", False):
        return {
            "id": channel["id"],
            "user": channel.get("user"),
        }
    else:
        return {
            "id": channel["id"],
            "name": channel.get("name"),
        }


def generate_summary(total_returned: int, has_next_cursor: bool) -> str:
    """Generate summary message for the response.

    Args:
        total_returned: Number of channels returned
        has_next_cursor: Whether there are more results available

    Returns:
        Summary message string
    """
    if has_next_cursor:
        return f"Found {total_returned} channels. More results available - please specify the cursor parameter to continue."
    return f"Found {total_returned} channels."


async def list_channels(
    limit: int | None = None,
    cursor: str | None = None,
    types: str | None = None,
    channel_name: str | None = None,
    user_id: str | None = None,
    response_format: str | None = None,
) -> dict[str, Any]:
    """List all channels the authenticated user has access to with optional filtering.

    This uses the user token to list channels, which means it can access:
    - Public channels in the workspace
    - Private channels the user is a member of
    - Direct messages (DMs)
    - Multi-party direct messages (group DMs)

    Args:
        limit: Maximum number of channels to return from API (default 100, max 200)
        cursor: Pagination cursor for next page of results
        types: Channel types to include (public_channel, private_channel, mpim, im)
        channel_name: Filter by channel name (case-insensitive partial match)
        user_id: Filter DMs by user ID (exact match, only for im type)
        response_format: Response format - "concise" (default) or "detailed"

    Returns:
        Dictionary containing:
        - ok: boolean
        - channels: filtered and formatted channel list
        - response_metadata: pagination info (if available)
        - summary: result summary with total count and helpful message
    """
    logger.info("Executing tool: slack_user_list_channels")

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

    if response_format is None:
        response_format = "concise"

    try:
        response = await make_slack_user_request("GET", "users.conversations", params=params)

        if not response.get("ok", False):
            return response

        channels = response.get("channels", [])
        filtered_channels = filter_channels(channels, channel_name, user_id)
        formatted_channels = [
            format_channel_response(ch, response_format) for ch in filtered_channels
        ]

        response_metadata = response.get("response_metadata", {})
        next_cursor = response_metadata.get("next_cursor", "")
        has_next_cursor = bool(next_cursor)

        result = {
            "ok": True,
            "channels": formatted_channels,
            "summary": {
                "total_returned": len(formatted_channels),
                "message": generate_summary(len(formatted_channels), has_next_cursor),
            },
        }

        if response_metadata:
            result["response_metadata"] = response_metadata

        return result
    except Exception as e:
        logger.exception(f"Error executing tool slack_user_list_channels: {e}")
        raise e

# get_channel_history returns the most recent messages from a channel
# User tokens: channels:history, groups:history, im:history, mpim:history
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
        return await make_slack_user_request("GET", "conversations.history", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool slack_get_channel_history: {e}")
        raise e

# invite_users_to_channel invites users to a channel
# User tokens: channels:write.invites, groups:write.invites, im:write.invites, mpim:write.invites
async def invite_users_to_channel(
    channel_id: str,
    user_ids: list[str]
) -> Dict[str, Any]:
    """Invite one or more users (including bot users) to a channel.

    This uses the user token to invite users to a channel. The authenticated user must have
    permission to invite users to the specified channel. Both regular users and bot users
    can be invited using their respective user IDs.

    Args:
        channel_id: The ID of the channel to invite users to (e.g., 'C1234567890')
        user_ids: A list of user IDs to invite (e.g., ['U1234567890', 'U9876543210'])

    Returns:
        Dictionary containing the updated channel information
    """
    logger.info(f"Executing tool: slack_invite_users_to_channel for channel {channel_id}")

    if not user_ids:
        raise ValueError("At least one user ID must be provided")

    # Slack API expects comma-separated user IDs
    data = {
        "channel": channel_id,
        "users": ",".join(user_ids)
    }

    try:
        return await make_slack_user_request("POST", "conversations.invite", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool slack_invite_users_to_channel: {e}")
        raise e
