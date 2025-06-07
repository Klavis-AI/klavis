from typing import Any, Dict
import logging

from .constants import WORKSPACE_OPT_FIELDS
from .base import (
    get_asana_client,
    get_next_page,
    remove_none_values,
    AsanaToolExecutionError,
)

logger = logging.getLogger(__name__)


async def get_workspace_by_id(
    workspace_id: str,
) -> Dict[str, Any]:
    """Get an Asana workspace by its ID"""
    try:
        client = get_asana_client()
        response = await client.get(f"/workspaces/{workspace_id}")
        return {"workspace": response["data"]}

    except AsanaToolExecutionError as e:
        logger.error(f"Asana API error: {e}")
        raise RuntimeError(f"Asana API Error: {e}")
    except Exception as e:
        logger.exception(f"Error executing get_workspace_by_id: {e}")
        raise e


async def list_workspaces(
    limit: int = 100,
    next_page_token: str | None = None,
) -> Dict[str, Any]:
    """List workspaces in Asana that are visible to the authenticated user"""
    try:
        limit = max(1, min(100, limit))

        client = get_asana_client()
        response = await client.get(
            "/workspaces",
            params=remove_none_values({
                "limit": limit,
                "offset": next_page_token,
                "opt_fields": ",".join(WORKSPACE_OPT_FIELDS),
            }),
        )

        return {
            "workspaces": response["data"],
            "count": len(response["data"]),
            "next_page": get_next_page(response),
        }

    except AsanaToolExecutionError as e:
        logger.error(f"Asana API error: {e}")
        raise RuntimeError(f"Asana API Error: {e}")
    except Exception as e:
        logger.exception(f"Error executing list_workspaces: {e}")
        raise e
