import logging
from typing import Any, Dict
logger = logging.getLogger(__name__)
from .base import _async_request, _async_paginate_get


async def get_lists() -> dict:
    """Get all lists (paginated)."""
    lists = await _async_paginate_get("/lists")
    return {"lists": lists}


async def get_list(list_id: str) -> dict:
    """Get a specific list by ID."""
    return await _async_request("GET", f"/lists/{list_id}")


async def create_list(list_name: str) -> dict:
    """Create a new Klaviyo list by name."""
    payload = {"data": {"type": "list", "attributes": {"name": list_name}}}
    return await _async_request("POST", "/lists", json=payload)


async def get_profiles_for_list(list_id: str) -> dict:
    """Get all profiles in a given list (paginated)."""
    profiles = await _async_paginate_get(f"/lists/{list_id}/relationships/profiles")
    return {"profiles": profiles}
