import logging
from typing import Any, Optional

from .base import (
    CloseToolExecutionError,
    ToolResponse,
    get_close_client,
    remove_none_values,
)
from .constants import CLOSE_MAX_LIMIT

logger = logging.getLogger(__name__)


async def list_notes(
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
    List note activities from Close CRM.
    
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
    
    response = await client.get("/activity/note/", params=params)
    
    return {
        "notes": response.get("data", []),
        "has_more": response.get("has_more", False),
        "total_results": response.get("total_results"),
    }


async def get_note(note_id: str) -> ToolResponse:
    """
    Get a specific note activity by ID.
    
    Args:
        note_id: The ID of the note to retrieve
    """
    
    client = get_close_client()
    
    response = await client.get(f"/activity/note/{note_id}/")
    
    return response


async def create_note(
    lead_id: str,
    note: str,
    user_id: Optional[str] = None,
    date_created: Optional[str] = None,
    **kwargs
) -> ToolResponse:
    """
    Create a new note activity in Close CRM.
    
    Args:
        lead_id: The ID of the lead this note belongs to
        note: Note text content
        user_id: The ID of the user creating the note
        date_created: Date the note was created (ISO 8601 format)
    """
    
    client = get_close_client()
    
    note_data = remove_none_values({
        "lead_id": lead_id,
        "note": note,
        "user_id": user_id,
        "date_created": date_created,
    })
    
    response = await client.post("/activity/note/", json_data=note_data)
    
    return response


async def update_note(
    note_id: str,
    note: Optional[str] = None,
    **kwargs
) -> ToolResponse:
    """
    Update an existing note activity.
    
    Args:
        note_id: The ID of the note to update
        note: Note text content
    """
    
    client = get_close_client()
    
    note_data = remove_none_values({
        "note": note,
    })
    
    if not note_data:
        raise CloseToolExecutionError("No update data provided")
    
    response = await client.put(f"/activity/note/{note_id}/", json_data=note_data)
    
    return response


async def delete_note(note_id: str) -> ToolResponse:
    """
    Delete a note activity.
    
    Args:
        note_id: The ID of the note to delete
    """
    
    client = get_close_client()
    
    response = await client.delete(f"/activity/note/{note_id}/")
    
    return {"success": True, "note_id": note_id}


async def search_notes(
    query: str,
    limit: Optional[int] = None,
    **kwargs
) -> ToolResponse:
    """
    Search for notes in Close CRM.
    
    Args:
        query: Search query string
        limit: Maximum number of results to return (1-200, default 25)
    """
    
    client = get_close_client()
    
    params = remove_none_values({
        "query": query,
        "_limit": min(limit, CLOSE_MAX_LIMIT) if limit else 25,
    })
    
    response = await client.get("/activity/note/", params=params)
    
    return {
        "notes": response.get("data", []),
        "has_more": response.get("has_more", False),
        "total_results": response.get("total_results"),
    }

