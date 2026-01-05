import logging
from typing import Any, Optional

from .base import (
    CloseToolExecutionError,
    ToolResponse,
    get_close_client,
    remove_none_values,
    normalize_activity,
)
from .constants import CLOSE_MAX_LIMIT

logger = logging.getLogger(__name__)


async def list_activities(
    limit: Optional[int] = None,
    skip: Optional[int] = None,
    lead_id: Optional[str] = None,
    user_id: Optional[str] = None,
    date_created__gte: Optional[str] = None,
    date_created__lte: Optional[str] = None,
    date_updated__gte: Optional[str] = None,
    date_updated__lte: Optional[str] = None,
    **kwargs
) -> ToolResponse:
    """
    List activities from Close CRM.
    
    Activities include emails, calls, SMS, notes, and meetings.
    
    Args:
        limit: Maximum number of results to return (1-200, default 100)
        skip: Number of results to skip for pagination
        lead_id: Filter by lead ID
        user_id: Filter by user ID
        date_created__gte: Filter by creation date (greater than or equal)
        date_created__lte: Filter by creation date (less than or equal)
        date_updated__gte: Filter by update date (greater than or equal)
        date_updated__lte: Filter by update date (less than or equal)
    """
    
    client = get_close_client()
    
    params = remove_none_values({
        "_limit": min(limit, CLOSE_MAX_LIMIT) if limit else 100,
        "_skip": skip,
        "lead_id": lead_id,
        "user_id": user_id,
        "date_created__gte": date_created__gte,
        "date_created__lte": date_created__lte,
        "date_updated__gte": date_updated__gte,
        "date_updated__lte": date_updated__lte,
    })
    
    response = await client.get("/activity/", params=params)
    
    return {
        "activities": [normalize_activity(a) for a in response.get("data", [])],
        "hasMore": response.get("has_more", False),
        "totalCount": response.get("total_results"),
    }


async def search_activities(
    query: str,
    limit: Optional[int] = None,
    **kwargs
) -> ToolResponse:
    """
    Search for activities in Close CRM.
    
    Args:
        query: Search query string
        limit: Maximum number of results to return (1-200, default 25)
    """
    
    client = get_close_client()
    
    params = remove_none_values({
        "query": query,
        "_limit": min(limit, CLOSE_MAX_LIMIT) if limit else 25,
    })
    
    response = await client.get("/activity/", params=params)
    
    return {
        "activities": [normalize_activity(a) for a in response.get("data", [])],
        "hasMore": response.get("has_more", False),
        "totalCount": response.get("total_results"),
    }
