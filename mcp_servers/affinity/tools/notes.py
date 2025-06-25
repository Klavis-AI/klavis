import logging
from typing import Any, Dict, Optional, List
from .base import make_http_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_notes(
    person_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    opportunity_id: Optional[int] = None,
    page_size: int = 10,
    page_token: Optional[str] = None
) -> Dict[str, Any]:
    """Get notes, optionally filtered by person, organization, or opportunity."""
    logger.info("Executing tool: get_notes")
    try:
        params = {
            "page_size": page_size
        }
        if person_id:
            params["person_id"] = person_id
        if organization_id:
            params["organization_id"] = organization_id
        if opportunity_id:
            params["opportunity_id"] = opportunity_id
        if page_token:
            params["page_token"] = page_token
        
        return await make_http_request("GET", "/notes", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool get_notes: {e}")
        raise e

async def get_note_by_id(note_id: int) -> Dict[str, Any]:
    """Get a specific note by ID."""
    logger.info(f"Executing tool: get_note_by_id with note_id: {note_id}")
    try:
        return await make_http_request("GET", f"/notes/{note_id}")
    except Exception as e:
        logger.exception(f"Error executing tool get_note_by_id: {e}")
        raise e

async def create_note(
    content: str,
    person_ids: Optional[List[int]] = None,
    organization_ids: Optional[List[int]] = None,
    opportunity_ids: Optional[List[int]] = None,
    parent_id: Optional[int] = None,
    type: int = 0
) -> Dict[str, Any]:
    """Create a new note."""
    logger.info("Executing tool: create_note")
    try:
        data = {
            "content": content,
            "type": type
        }
        if person_ids:
            data["person_ids"] = person_ids
        if organization_ids:
            data["organization_ids"] = organization_ids
        if opportunity_ids:
            data["opportunity_ids"] = opportunity_ids
        if parent_id:
            data["parent_id"] = parent_id
        
        return await make_http_request("POST", "/notes", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool create_note: {e}")
        raise e

async def update_note(
    note_id: int,
    content: str
) -> Dict[str, Any]:
    """Update an existing note."""
    logger.info(f"Executing tool: update_note with note_id: {note_id}")
    try:
        data = {
            "content": content
        }
        return await make_http_request("PUT", f"/notes/{note_id}", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool update_note: {e}")
        raise e

async def delete_note(note_id: int) -> Dict[str, Any]:
    """Delete a note."""
    logger.info(f"Executing tool: delete_note with note_id: {note_id}")
    try:
        return await make_http_request("DELETE", f"/notes/{note_id}")
    except Exception as e:
        logger.exception(f"Error executing tool delete_note: {e}")
        raise e 