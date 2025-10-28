import logging
from typing import Any, Dict, List, Optional

from .base import (
    CloseToolExecutionError,
    ToolResponse,
    get_close_client,
    remove_none_values,
    format_leads_response,
)
from .constants import CLOSE_MAX_LIMIT

logger = logging.getLogger(__name__)


async def list_leads(
    limit: Optional[int] = None,
    skip: Optional[int] = None,
    query: Optional[str] = None,
    status_id: Optional[str] = None,
    **kwargs
) -> ToolResponse:
    """List leads from Close CRM."""
    
    client = get_close_client()
    
    params = remove_none_values({
        "_limit": min(limit, CLOSE_MAX_LIMIT) if limit else 100,
        "_skip": skip,
        "query": query,
        "status_id": status_id,
    })
    
    response = await client.get("/lead/", params=params)
    
    result = {
        "leads": response.get("data", []),
        "has_more": response.get("has_more", False),
        "total_results": response.get("total_results"),
    }
    
    return format_leads_response(result)


async def get_lead(lead_id: str, fields: Optional[str] = None) -> ToolResponse:
    """Get a specific lead by ID."""
    
    client = get_close_client()
    
    params = remove_none_values({
        "_fields": fields,
    })
    
    response = await client.get(f"/lead/{lead_id}/", params=params)
    
    # Format opportunities if they exist in the lead
    if 'opportunities' in response:
        result = {"leads": [response]}
        formatted = format_leads_response(result)
        return formatted["leads"][0]
    
    return response


async def create_lead(
    name: str,
    description: Optional[str] = None,
    status_id: Optional[str] = None,
    contacts: Optional[List[Dict[str, Any]]] = None,
    addresses: Optional[List[Dict[str, Any]]] = None,
    url: Optional[str] = None,
    **custom_fields
) -> ToolResponse:
    """Create a new lead in Close CRM."""
    
    client = get_close_client()
    
    lead_data = remove_none_values({
        "name": name,
        "description": description,
        "status_id": status_id,
        "contacts": contacts,
        "addresses": addresses,
        "url": url,
        **custom_fields
    })
    
    response = await client.post("/lead/", json_data=lead_data)
    
    return response


async def update_lead(
    lead_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    status_id: Optional[str] = None,
    url: Optional[str] = None,
    **custom_fields
) -> ToolResponse:
    """Update an existing lead."""
    
    client = get_close_client()
    
    lead_data = remove_none_values({
        "name": name,
        "description": description,
        "status_id": status_id,
        "url": url,
        **custom_fields
    })
    
    if not lead_data:
        raise CloseToolExecutionError("No update data provided")
    
    response = await client.put(f"/lead/{lead_id}/", json_data=lead_data)
    
    return response


async def delete_lead(lead_id: str) -> ToolResponse:
    """Delete a lead."""
    
    client = get_close_client()
    
    response = await client.delete(f"/lead/{lead_id}/")
    
    return {"success": True, "lead_id": lead_id}


async def search_leads(
    query: str,
    limit: Optional[int] = None,
    fields: Optional[str] = None,
    **kwargs
) -> ToolResponse:
    """Search for leads using Close CRM search."""
    
    client = get_close_client()
    
    params = remove_none_values({
        "query": query,
        "_limit": min(limit, CLOSE_MAX_LIMIT) if limit else 25,
        "_fields": fields,
    })
    
    response = await client.get("/lead/", params=params)
    
    result = {
        "leads": response.get("data", []),
        "has_more": response.get("has_more", False),
        "total_results": response.get("total_results"),
    }
    
    return format_leads_response(result)


async def merge_leads(
    source_lead_id: str,
    destination_lead_id: str
) -> ToolResponse:
    """Merge two leads."""
    
    client = get_close_client()
    
    merge_data = {
        "source": source_lead_id,
        "destination": destination_lead_id,
    }
    
    response = await client.post("/lead/merge/", json_data=merge_data)
    
    return response 