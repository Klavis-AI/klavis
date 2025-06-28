import logging
from typing import Any, Dict, Optional, List
from .base import make_http_request

# Configure logging
logger = logging.getLogger(__name__)

async def search_opportunities(
    term: Optional[str] = None,
    page_size: int = 10,
    page_token: Optional[str] = None
) -> Dict[str, Any]:
    """Search for opportunities."""
    logger.info(f"Executing tool: search_opportunities with term: {term}")
    try:
        params = {
            "page_size": page_size
        }
        if term:
            params["term"] = term
        if page_token:
            params["page_token"] = page_token
        
        return await make_http_request("GET", "/opportunities", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool search_opportunities: {e}")
        raise e

async def get_opportunity_by_id(opportunity_id: int) -> Dict[str, Any]:
    """Get a specific opportunity by ID."""
    logger.info(f"Executing tool: get_opportunity_by_id with opportunity_id: {opportunity_id}")
    try:
        return await make_http_request("GET", f"/opportunities/{opportunity_id}")
    except Exception as e:
        logger.exception(f"Error executing tool get_opportunity_by_id: {e}")
        raise e

async def create_opportunity(
    name: str,
    person_ids: Optional[List[int]] = None,
    organization_ids: Optional[List[int]] = None
) -> Dict[str, Any]:
    """Create a new opportunity."""
    logger.info(f"Executing tool: create_opportunity with name: {name}")
    try:
        data = {
            "name": name
        }
        if person_ids:
            data["person_ids"] = person_ids
        if organization_ids:
            data["organization_ids"] = organization_ids
        
        return await make_http_request("POST", "/opportunities", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool create_opportunity: {e}")
        raise e

async def update_opportunity(
    opportunity_id: int,
    name: Optional[str] = None,
    person_ids: Optional[List[int]] = None,
    organization_ids: Optional[List[int]] = None
) -> Dict[str, Any]:
    """Update an existing opportunity."""
    logger.info(f"Executing tool: update_opportunity with opportunity_id: {opportunity_id}")
    try:
        data = {}
        if name:
            data["name"] = name
        if person_ids:
            data["person_ids"] = person_ids
        if organization_ids:
            data["organization_ids"] = organization_ids
        
        return await make_http_request("PUT", f"/opportunities/{opportunity_id}", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool update_opportunity: {e}")
        raise e

async def delete_opportunity(opportunity_id: int) -> Dict[str, Any]:
    """Delete an opportunity."""
    logger.info(f"Executing tool: delete_opportunity with opportunity_id: {opportunity_id}")
    try:
        return await make_http_request("DELETE", f"/opportunities/{opportunity_id}")
    except Exception as e:
        logger.exception(f"Error executing tool delete_opportunity: {e}")
        raise e 