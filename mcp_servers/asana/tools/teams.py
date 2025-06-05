from typing import Annotated, Any, Dict
import logging

from .constants import TEAM_OPT_FIELDS
from .base import (
    get_asana_client,
    get_next_page,
    get_unique_workspace_id_or_raise_error,
    remove_none_values,
    AsanaToolExecutionError,
)

logger = logging.getLogger(__name__)


async def get_team_by_id(
    team_id: str,
) -> Dict[str, Any]:
    """Get an Asana team by its ID"""
    try:
        client = get_asana_client()
        response = await client.get(
            f"/teams/{team_id}",
            params=remove_none_values({"opt_fields": ",".join(TEAM_OPT_FIELDS)}),
        )
        return {"team": response["data"]}

    except AsanaToolExecutionError as e:
        logger.error(f"Asana API error: {e}")
        raise RuntimeError(f"Asana API Error: {e}")
    except Exception as e:
        logger.exception(f"Error executing get_team_by_id: {e}")
        raise e


async def list_teams_the_current_user_is_a_member_of(
    workspace_id: str | None = None,
    limit: int = 100,
    next_page_token: str | None = None,
) -> Dict[str, Any]:
    """List teams in Asana that the current user is a member of"""
    try:
        limit = max(1, min(100, limit))

        workspace_id = workspace_id or await get_unique_workspace_id_or_raise_error()

        client = get_asana_client()
        response = await client.get(
            "/users/me/teams",
            params=remove_none_values({
                "limit": limit,
                "offset": next_page_token,
                "opt_fields": ",".join(TEAM_OPT_FIELDS),
                "organization": workspace_id,
            }),
        )

        return {
            "teams": response["data"],
            "count": len(response["data"]),
            "next_page": get_next_page(response),
        }

    except AsanaToolExecutionError as e:
        logger.error(f"Asana API error: {e}")
        raise RuntimeError(f"Asana API Error: {e}")
    except Exception as e:
        logger.exception(f"Error executing list_teams_the_current_user_is_a_member_of: {e}")
        raise e


async def list_teams(
    workspace_id: str | None = None,
    limit: int = 100,
    next_page_token: str | None = None,
) -> Dict[str, Any]:
    """List teams in an Asana workspace"""
    try:
        limit = max(1, min(100, limit))

        workspace_id = workspace_id or await get_unique_workspace_id_or_raise_error()

        client = get_asana_client()
        response = await client.get(
            f"/workspaces/{workspace_id}/teams",
            params=remove_none_values({
                "limit": limit,
                "offset": next_page_token,
                "opt_fields": ",".join(TEAM_OPT_FIELDS),
            }),
        )

        return {
            "teams": response["data"],
            "count": len(response["data"]),
            "next_page": get_next_page(response),
        }

    except AsanaToolExecutionError as e:
        logger.error(f"Asana API error: {e}")
        raise RuntimeError(f"Asana API Error: {e}")
    except Exception as e:
        logger.exception(f"Error executing list_teams: {e}")
        raise e
