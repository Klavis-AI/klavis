from typing import Annotated, Any, Dict
import logging

from .constants import PROJECT_OPT_FIELDS
from .base import (
    get_asana_client,
    get_next_page,
    get_unique_workspace_id_or_raise_error,
    remove_none_values,
    AsanaToolExecutionError,
)

logger = logging.getLogger(__name__)


async def get_project_by_id(
    project_id: str,
) -> Dict[str, Any]:
    """Get a project by its ID"""
    try:
        client = get_asana_client()
        response = await client.get(
            f"/projects/{project_id}",
            params={"opt_fields": ",".join(PROJECT_OPT_FIELDS)},
        )
        return {"project": response["data"]}

    except AsanaToolExecutionError as e:
        logger.error(f"Asana API error: {e}")
        raise RuntimeError(f"Asana API Error: {e}")
    except Exception as e:
        logger.exception(f"Error executing get_project_by_id: {e}")
        raise e


async def list_projects(
    team_id: str | None = None,
    workspace_id: str | None = None,
    limit: int = 100,
    next_page_token: str | None = None,
) -> Dict[str, Any]:
    """List projects in Asana"""
    try:
        # Note: Asana recommends filtering by team to avoid timeout in large domains.
        # Ref: https://developers.asana.com/reference/getprojects
        limit = max(1, min(100, limit))

        workspace_id = workspace_id or await get_unique_workspace_id_or_raise_error()

        client = get_asana_client()

        response = await client.get(
            "/projects",
            params=remove_none_values({
                "limit": limit,
                "offset": next_page_token,
                "team": team_id,
                "workspace": workspace_id,
                "opt_fields": ",".join(PROJECT_OPT_FIELDS),
            }),
        )

        return {
            "projects": response["data"],
            "count": len(response["data"]),
            "next_page": get_next_page(response),
        }

    except AsanaToolExecutionError as e:
        logger.error(f"Asana API error: {e}")
        raise RuntimeError(f"Asana API Error: {e}")
    except Exception as e:
        logger.exception(f"Error executing list_projects: {e}")
        raise e
