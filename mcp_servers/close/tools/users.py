import logging
from typing import Any, Dict, List, Optional

from .base import (
    CloseToolExecutionError,
    ToolResponse,
    get_close_client,
    remove_none_values,
    normalize_user,
)
from .constants import CLOSE_MAX_LIMIT

logger = logging.getLogger(__name__)


async def get_current_user() -> ToolResponse:
    """Get the current user information."""
    
    client = get_close_client()
    
    response = await client.get_current_user()
    
    return {"user": normalize_user(response)}


async def list_users(
    limit: Optional[int] = None,
    skip: Optional[int] = None,
    **kwargs
) -> ToolResponse:
    """List users from Close CRM."""
    
    client = get_close_client()
    
    params = remove_none_values({
        "_limit": min(limit, CLOSE_MAX_LIMIT) if limit else 100,
        "_skip": skip,
    })
    
    response = await client.get("/user/", params=params)
    
    return {
        "users": [normalize_user(u) for u in response.get("data", [])],
        "hasMore": response.get("has_more", False),
        "totalCount": response.get("total_results"),
    }


async def get_user(user_id: str) -> ToolResponse:
    """Get a specific user by ID."""
    
    client = get_close_client()
    
    response = await client.get(f"/user/{user_id}/")
    
    return {"user": normalize_user(response)}


async def search_users(
    query: str,
    limit: Optional[int] = None,
    **kwargs
) -> ToolResponse:
    """Search for users using Close CRM search."""
    
    client = get_close_client()
    
    params = remove_none_values({
        "query": query,
        "_limit": min(limit, CLOSE_MAX_LIMIT) if limit else 25,
    })
    
    response = await client.get("/user/", params=params)
    
    return {
        "users": [normalize_user(u) for u in response.get("data", [])],
        "hasMore": response.get("has_more", False),
        "totalCount": response.get("total_results"),
    } 