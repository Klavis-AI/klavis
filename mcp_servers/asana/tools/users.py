from typing import Annotated, Any, Dict
import logging

from .constants import USER_OPT_FIELDS
from .base import (
    get_asana_client,
    get_next_page,
    get_unique_workspace_id_or_raise_error,
    remove_none_values,
    AsanaToolExecutionError,
)

logger = logging.getLogger(__name__)


async def list_users(
    workspace_id: str | None = None,
    limit: int = 100,
    next_page_token: str | None = None,
) -> Dict[str, Any]:
    """List users in Asana"""
    try:
        limit = max(1, min(100, limit))

        if not workspace_id:
            workspace_id = await get_unique_workspace_id_or_raise_error()

        client = get_asana_client()
        response = await client.get(
            "/users",
            params=remove_none_values({
                "workspace": workspace_id,
                "limit": limit,
                "offset": next_page_token,
                "opt_fields": ",".join(USER_OPT_FIELDS),
            }),
        )

        return {
            "users": response["data"],
            "count": len(response["data"]),
            "next_page": get_next_page(response),
        }

    except AsanaToolExecutionError as e:
        logger.error(f"Asana API error: {e}")
        raise RuntimeError(f"Asana API Error: {e}")
    except Exception as e:
        logger.exception(f"Error executing list_users: {e}")
        raise e


async def get_user_by_id(
    user_id: str,
) -> Dict[str, Any]:
    """Get a user by ID"""
    try:
        client = get_asana_client()
        response = await client.get(f"/users/{user_id}", params={"opt_fields": ",".join(USER_OPT_FIELDS)})
        return {"user": response["data"]}

    except AsanaToolExecutionError as e:
        logger.error(f"Asana API error: {e}")
        raise RuntimeError(f"Asana API Error: {e}")
    except Exception as e:
        logger.exception(f"Error executing get_user_by_id: {e}")
        raise e
