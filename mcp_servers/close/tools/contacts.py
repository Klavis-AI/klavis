import logging
from typing import Any, Dict, List, Optional

from .base import (
    CloseToolExecutionError,
    ToolResponse,
    get_close_client,
    remove_none_values,
)
from .constants import CLOSE_MAX_LIMIT

logger = logging.getLogger(__name__)


async def list_contacts(
    limit: Optional[int] = None,
    skip: Optional[int] = None,
    lead_id: Optional[str] = None,
    query: Optional[str] = None,
    **kwargs
) -> ToolResponse:
    """List contacts from Close CRM."""
    
    client = get_close_client()
    
    params = remove_none_values({
        "_limit": min(limit, CLOSE_MAX_LIMIT) if limit else 100,
        "_skip": skip,
        "lead_id": lead_id,
        "query": query,
    })
    
    response = await client.get("/contact/", params=params)
    
    return {
        "contacts": response.get("data", []),
        "has_more": response.get("has_more", False),
        "total_results": response.get("total_results"),
    }


async def get_contact(contact_id: str) -> ToolResponse:
    """Get a specific contact by ID."""
    
    client = get_close_client()
    
    response = await client.get(f"/contact/{contact_id}/")
    
    return response


async def create_contact(
    lead_id: str,
    name: Optional[str] = None,
    title: Optional[str] = None,
    emails: Optional[List[Dict[str, Any]]] = None,
    phones: Optional[List[Dict[str, Any]]] = None,
    urls: Optional[List[Dict[str, Any]]] = None,
    **custom_fields
) -> ToolResponse:
    """Create a new contact in Close CRM."""
    
    client = get_close_client()
    
    contact_data = remove_none_values({
        "lead_id": lead_id,
        "name": name,
        "title": title,
        "emails": emails,
        "phones": phones,
        "urls": urls,
        **custom_fields
    })
    
    response = await client.post("/contact/", json_data=contact_data)
    
    return response


async def update_contact(
    contact_id: str,
    name: Optional[str] = None,
    title: Optional[str] = None,
    emails: Optional[List[Dict[str, Any]]] = None,
    phones: Optional[List[Dict[str, Any]]] = None,
    urls: Optional[List[Dict[str, Any]]] = None,
    **custom_fields
) -> ToolResponse:
    """Update an existing contact."""
    
    client = get_close_client()
    
    contact_data = remove_none_values({
        "name": name,
        "title": title,
        "emails": emails,
        "phones": phones,
        "urls": urls,
        **custom_fields
    })
    
    if not contact_data:
        raise CloseToolExecutionError("No update data provided")
    
    response = await client.put(f"/contact/{contact_id}/", json_data=contact_data)
    
    return response


async def delete_contact(contact_id: str) -> ToolResponse:
    """Delete a contact."""
    
    client = get_close_client()
    
    response = await client.delete(f"/contact/{contact_id}/")
    
    return {"success": True, "contact_id": contact_id}


async def search_contacts(
    query: str,
    limit: Optional[int] = None,
    **kwargs
) -> ToolResponse:
    """Search for contacts using Close CRM search."""
    
    client = get_close_client()
    
    params = remove_none_values({
        "query": query,
        "_limit": min(limit, CLOSE_MAX_LIMIT) if limit else 25,
    })
    
    response = await client.get("/contact/", params=params)
    
    return {
        "contacts": response.get("data", []),
        "has_more": response.get("has_more", False),
        "total_results": response.get("total_results"),
    } 