import logging
from typing import Any

from .base import make_slack_user_request

logger = logging.getLogger(__name__)


def filter_users(
    users: list[dict[str, Any]],
    user_id: str | None = None,
    name: str | None = None,
) -> list[dict[str, Any]]:
    """Client-side filtering of users.

    Args:
        users: Raw user list from Slack API
        user_id: Optional user ID filter (exact match)
        name: Optional name filter (case-insensitive partial match against name or real_name)

    Returns:
        Filtered list of users (duplicates removed)
    """
    if not user_id and not name:
        return users

    filtered = []
    seen_ids = set()

    if user_id:
        for user in users:
            if user.get("id") == user_id:
                user_id_val = user.get("id")
                if user_id_val and user_id_val not in seen_ids:
                    filtered.append(user)
                    seen_ids.add(user_id_val)

    if name:
        name_lower = name.lower()
        for user in users:
            user_id_val = user.get("id")
            if (
                user_id_val
                and user_id_val not in seen_ids
                and (
                    name_lower in user.get("name", "").lower()
                    or name_lower in user.get("real_name", "").lower()
                )
            ):
                filtered.append(user)
                seen_ids.add(user_id_val)

    return filtered


def format_user_response(
    user: dict[str, Any],
    response_format: str = "concise",
) -> dict[str, Any]:
    """Format a single user object based on response_format.

    Args:
        user: Raw user object from Slack API
        response_format: "concise" or "detailed"

    Returns:
        Formatted user object
    """
    if response_format == "detailed":
        return user

    return {
        "id": user["id"],
        "name": user.get("name"),
        "real_name": user.get("real_name"),
    }


def generate_summary(total_returned: int, has_next_cursor: bool) -> str:
    """Generate summary message for the response.

    Args:
        total_returned: Number of users returned
        has_next_cursor: Whether there are more results available

    Returns:
        Summary message string
    """
    if has_next_cursor:
        return f"Found {total_returned} users. More results available - please specify the cursor parameter to continue."
    return f"Found {total_returned} users."


async def list_users(
    cursor: str | None = None,
    limit: int | None = None,
    team_id: str | None = None,
    include_locale: bool | None = None,
    user_id: str | None = None,
    name: str | None = None,
    response_format: str | None = None,
) -> dict[str, Any]:
    """Lists all users in a Slack team with optional filtering.

    This uses the user token to list users, which means it can access:
    - All users in the workspace (including deleted and bot users)

    Args:
        cursor: Pagination cursor for next page of results
        limit: Maximum number of users to return from API (default 100, max 200)
        team_id: Team ID to list users from (for Enterprise Grid)
        include_locale: Whether to include locale information for each user
        user_id: Filter by user ID (exact match)
        name: Filter by name (case-insensitive partial match against name or real_name)
        response_format: Response format - "concise" (default) or "detailed"

    Returns:
        Dictionary containing:
        - ok: boolean
        - members: filtered and formatted user list
        - response_metadata: pagination info (if available)
        - summary: result summary with total count and helpful message
    """
    logger.info("Executing tool: list_users")

    params = {}

    if limit:
        params["limit"] = str(min(limit, 200))
    else:
        params["limit"] = "100"

    if cursor:
        params["cursor"] = cursor

    if team_id:
        params["team_id"] = team_id

    if include_locale is not None:
        params["include_locale"] = str(include_locale).lower()

    if response_format is None:
        response_format = "concise"

    try:
        response = await make_slack_user_request("GET", "users.list", params=params)

        if not response.get("ok", False):
            return response

        members = response.get("members", [])
        filtered_members = filter_users(members, user_id, name)
        formatted_members = [
            format_user_response(user, response_format) for user in filtered_members
        ]

        response_metadata = response.get("response_metadata", {})
        next_cursor = response_metadata.get("next_cursor", "")
        has_next_cursor = bool(next_cursor)

        result = {
            "ok": True,
            "members": formatted_members,
            "summary": {
                "total_returned": len(formatted_members),
                "message": generate_summary(len(formatted_members), has_next_cursor),
            },
        }

        if response_metadata:
            result["response_metadata"] = response_metadata

        return result
    except Exception as e:
        logger.exception(f"Error executing tool list_users: {e}")
        raise e

# Gets information about a user.
# User tokens: users:read
async def user_get_info(
    user_id: str,
    include_locale: Optional[bool] = None
) -> Dict[str, Any]:
    """Gets information about a user using users.info API."""
    logger.info(f"Executing tool: user_get_info for user {user_id}")

    params = {
        "user": user_id
    }

    # Include locale information
    if include_locale is not None:
        params["include_locale"] = str(include_locale).lower()

    try:
        return await make_slack_user_request("GET", "users.info", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool user_get_info: {e}")
        raise e
