import logging
from typing import Any, Dict, List, Optional

from .base import (
    CloseToolExecutionError,
    ToolResponse,
    get_close_client,
    remove_none_values,
    format_opportunity_values,
)
from .constants import CLOSE_MAX_LIMIT

logger = logging.getLogger(__name__)


async def list_opportunities(
    limit: Optional[int] = None,
    skip: Optional[int] = None,
    lead_id: Optional[str] = None,
    status_id: Optional[str] = None,
    **kwargs
) -> ToolResponse:
    """List opportunities from Close CRM."""
    
    client = get_close_client()
    
    params = remove_none_values({
        "_limit": min(limit, CLOSE_MAX_LIMIT) if limit else 100,
        "_skip": skip,
        "lead_id": lead_id,
        "status_id": status_id,
    })
    
    response = await client.get("/opportunity/", params=params)
    
    # Format monetary values in opportunities
    formatted_opportunities = []
    for opp in response.get("data", []):
        formatted_opportunities.append(format_opportunity_values(opp))
    
    return {
        "opportunities": formatted_opportunities,
        "has_more": response.get("has_more", False),
        "total_results": response.get("total_results"),
    }


async def get_opportunity(opportunity_id: str) -> ToolResponse:
    """Get a specific opportunity by ID."""
    
    client = get_close_client()
    
    response = await client.get(f"/opportunity/{opportunity_id}/")
    
    return format_opportunity_values(response)


async def create_opportunity(
    lead_id: str,
    note: Optional[str] = None,
    confidence: Optional[int] = None,
    value: Optional[float] = None,
    value_period: Optional[str] = None,
    status_id: Optional[str] = None,
    expected_date: Optional[str] = None,
    **custom_fields
) -> ToolResponse:
    """Create a new opportunity in Close CRM."""
    
    client = get_close_client()
    
    opportunity_data = remove_none_values({
        "lead_id": lead_id,
        "note": note,
        "confidence": confidence,
        "value": value,
        "value_period": value_period,
        "status_id": status_id,
        "expected_date": expected_date,
        **custom_fields
    })
    
    response = await client.post("/opportunity/", json_data=opportunity_data)
    
    return format_opportunity_values(response)


async def update_opportunity(
    opportunity_id: str,
    note: Optional[str] = None,
    confidence: Optional[int] = None,
    value: Optional[float] = None,
    value_period: Optional[str] = None,
    status_id: Optional[str] = None,
    expected_date: Optional[str] = None,
    **custom_fields
) -> ToolResponse:
    """Update an existing opportunity."""
    
    client = get_close_client()
    
    opportunity_data = remove_none_values({
        "note": note,
        "confidence": confidence,
        "value": value,
        "value_period": value_period,
        "status_id": status_id,
        "expected_date": expected_date,
        **custom_fields
    })
    
    if not opportunity_data:
        raise CloseToolExecutionError("No update data provided")
    
    response = await client.put(f"/opportunity/{opportunity_id}/", json_data=opportunity_data)
    
    return format_opportunity_values(response)


async def delete_opportunity(opportunity_id: str) -> ToolResponse:
    """Delete an opportunity."""
    
    client = get_close_client()
    
    response = await client.delete(f"/opportunity/{opportunity_id}/")
    
    return {"success": True, "opportunity_id": opportunity_id}


async def search_opportunities(
    query: str,
    limit: Optional[int] = None,
    **kwargs
) -> ToolResponse:
    """Search for opportunities using Close CRM search."""
    
    client = get_close_client()
    
    params = remove_none_values({
        "query": query,
        "_limit": min(limit, CLOSE_MAX_LIMIT) if limit else 25,
    })
    
    response = await client.get("/opportunity/", params=params)
    
    # Format monetary values in opportunities
    formatted_opportunities = []
    for opp in response.get("data", []):
        formatted_opportunities.append(format_opportunity_values(opp))
    
    return {
        "opportunities": formatted_opportunities,
        "has_more": response.get("has_more", False),
        "total_results": response.get("total_results"),
    } 