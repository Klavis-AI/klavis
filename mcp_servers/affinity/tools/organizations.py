import logging
from typing import Any, Dict, Optional, List
from .base import make_http_request

# Configure logging
logger = logging.getLogger(__name__)

async def search_organizations(
    term: Optional[str] = None,
    page_size: int = 10,
    page_token: Optional[str] = None
) -> Dict[str, Any]:
    """Search for organizations."""
    logger.info(f"Executing tool: search_organizations with term: {term}")
    try:
        params = {
            "page_size": page_size
        }
        if term:
            params["term"] = term
        if page_token:
            params["page_token"] = page_token
        
        return await make_http_request("GET", "/organizations", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool search_organizations: {e}")
        raise e

async def get_organization_by_id(organization_id: int) -> Dict[str, Any]:
    """Get a specific organization by ID."""
    logger.info(f"Executing tool: get_organization_by_id with organization_id: {organization_id}")
    try:
        return await make_http_request("GET", f"/organizations/{organization_id}")
    except Exception as e:
        logger.exception(f"Error executing tool get_organization_by_id: {e}")
        raise e

async def create_organization(
    name: str,
    domain: Optional[str] = None,
    person_ids: Optional[List[int]] = None
) -> Dict[str, Any]:
    """Create a new organization."""
    logger.info(f"Executing tool: create_organization with name: {name}")
    try:
        data = {
            "name": name
        }
        if domain:
            data["domain"] = domain
        if person_ids:
            data["person_ids"] = person_ids
        
        return await make_http_request("POST", "/organizations", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool create_organization: {e}")
        raise e

async def update_organization(
    organization_id: int,
    name: Optional[str] = None,
    domain: Optional[str] = None,
    person_ids: Optional[List[int]] = None
) -> Dict[str, Any]:
    """Update an existing organization."""
    logger.info(f"Executing tool: update_organization with organization_id: {organization_id}")
    try:
        data = {}
        if name:
            data["name"] = name
        if domain:
            data["domain"] = domain
        if person_ids:
            data["person_ids"] = person_ids
        
        return await make_http_request("PUT", f"/organizations/{organization_id}", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool update_organization: {e}")
        raise e

async def delete_organization(organization_id: int) -> Dict[str, Any]:
    """Delete an organization."""
    logger.info(f"Executing tool: delete_organization with organization_id: {organization_id}")
    try:
        return await make_http_request("DELETE", f"/organizations/{organization_id}")
    except Exception as e:
        logger.exception(f"Error executing tool delete_organization: {e}")
        raise e 