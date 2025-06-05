from typing import Annotated, Any, Dict
import logging

from .constants import TAG_OPT_FIELDS, TagColor
from .base import (
    get_asana_client,
    get_next_page,
    get_unique_workspace_id_or_raise_error,
    remove_none_values,
    AsanaToolExecutionError,
)

logger = logging.getLogger(__name__)


async def get_tag_by_id(
    tag_id: str,
) -> Dict[str, Any]:
    """Get an Asana tag by its ID"""
    try:
        client = get_asana_client()
        response = await client.get(f"/tags/{tag_id}")
        return {"tag": response["data"]}

    except AsanaToolExecutionError as e:
        logger.error(f"Asana API error: {e}")
        raise RuntimeError(f"Asana API Error: {e}")
    except Exception as e:
        logger.exception(f"Error executing get_tag_by_id: {e}")
        raise e


async def create_tag(
    name: str,
    description: str | None = None,
    color: TagColor | None = None,
    workspace_id: str | None = None,
) -> Dict[str, Any]:
    """Create a tag in Asana"""
    try:
        if not 1 <= len(name) <= 100:
            raise ValueError("Tag name must be between 1 and 100 characters long.")

        workspace_id = workspace_id or await get_unique_workspace_id_or_raise_error()

        data = remove_none_values({
            "name": name,
            "notes": description,
            "color": color.value if color else None,
            "workspace": workspace_id,
        })

        client = get_asana_client()
        response = await client.post("/tags", json_data={"data": data})
        return {"tag": response["data"]}

    except AsanaToolExecutionError as e:
        logger.error(f"Asana API error: {e}")
        raise RuntimeError(f"Asana API Error: {e}")
    except Exception as e:
        logger.exception(f"Error executing create_tag: {e}")
        raise e


async def list_tags(
    workspace_id: str | None = None,
    limit: int = 100,
    next_page_token: str | None = None,
) -> Dict[str, Any]:
    """List tags in an Asana workspace"""
    try:
        limit = max(1, min(100, limit))

        workspace_id = workspace_id or await get_unique_workspace_id_or_raise_error()

        client = get_asana_client()
        response = await client.get(
            "/tags",
            params=remove_none_values({
                "limit": limit,
                "offset": next_page_token,
                "workspace": workspace_id,
                "opt_fields": ",".join(TAG_OPT_FIELDS),
            }),
        )

        return {
            "tags": response["data"],
            "count": len(response["data"]),
            "next_page": get_next_page(response),
        }

    except AsanaToolExecutionError as e:
        logger.error(f"Asana API error: {e}")
        raise RuntimeError(f"Asana API Error: {e}")
    except Exception as e:
        logger.exception(f"Error executing list_tags: {e}")
        raise e
