import logging
from typing import Optional, Dict, Any, List
from .base import make_zendesk_request, validate_pagination_params, ZendeskToolExecutionError

logger = logging.getLogger(__name__)

async def list_organizations(
    page: Optional[int] = None,
    per_page: Optional[int] = None
) -> Dict[str, Any]:
    """List organizations with pagination."""
    try:
        params = validate_pagination_params(page, per_page)
        return await make_zendesk_request("GET", "/organizations.json", params=params)
    except Exception as e:
        logger.error(f"Error listing organizations: {e}")
        raise

async def get_organization(organization_id: int) -> Dict[str, Any]:
    """Get a single organization by ID."""
    try:
        if not organization_id or organization_id <= 0:
            raise ZendeskToolExecutionError("Valid organization ID is required")
        
        return await make_zendesk_request("GET", f"/organizations/{organization_id}.json")
    except Exception as e:
        logger.error(f"Error getting organization {organization_id}: {e}")
        raise

async def create_organization(
    name: str,
    domain: Optional[str] = None,
    tags: Optional[List[str]] = None,
    custom_fields: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Create a new organization."""
    try:
        if not name:
            raise ZendeskToolExecutionError("Organization name is required")
        
        org_data = {
            "organization": {
                "name": name
            }
        }
        
        # Add optional fields
        if domain:
            org_data["organization"]["domain"] = domain
        if tags:
            org_data["organization"]["tags"] = tags
        if custom_fields:
            org_data["organization"]["custom_fields"] = custom_fields
        
        return await make_zendesk_request("POST", "/organizations.json", data=org_data)
    except Exception as e:
        logger.error(f"Error creating organization: {e}")
        raise

async def update_organization(
    organization_id: int,
    name: Optional[str] = None,
    domain: Optional[str] = None,
    tags: Optional[List[str]] = None,
    custom_fields: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Update an existing organization."""
    try:
        if not organization_id or organization_id <= 0:
            raise ZendeskToolExecutionError("Valid organization ID is required")
        
        org_data = {"organization": {}}
        
        # Add only provided fields
        if name is not None:
            org_data["organization"]["name"] = name
        if domain is not None:
            org_data["organization"]["domain"] = domain
        if tags is not None:
            org_data["organization"]["tags"] = tags
        if custom_fields is not None:
            org_data["organization"]["custom_fields"] = custom_fields
        
        return await make_zendesk_request("PUT", f"/organizations/{organization_id}.json", data=org_data)
    except Exception as e:
        logger.error(f"Error updating organization {organization_id}: {e}")
        raise

async def delete_organization(organization_id: int) -> Dict[str, Any]:
    """Delete an organization."""
    try:
        if not organization_id or organization_id <= 0:
            raise ZendeskToolExecutionError("Valid organization ID is required")
        
        return await make_zendesk_request("DELETE", f"/organizations/{organization_id}.json")
    except Exception as e:
        logger.error(f"Error deleting organization {organization_id}: {e}")
        raise

async def search_organizations(
    query: str,
    page: Optional[int] = None,
    per_page: Optional[int] = None
) -> Dict[str, Any]:
    """Search organizations using Zendesk search syntax."""
    try:
        if not query:
            raise ZendeskToolExecutionError("Search query is required")
        
        params = validate_pagination_params(page, per_page)
        params["query"] = query
        
        return await make_zendesk_request("GET", "/search.json", params=params)
    except Exception as e:
        logger.error(f"Error searching organizations with query '{query}': {e}")
        raise

async def get_organization_tickets(
    organization_id: int,
    page: Optional[int] = None,
    per_page: Optional[int] = None
) -> Dict[str, Any]:
    """Get tickets for a specific organization."""
    try:
        if not organization_id or organization_id <= 0:
            raise ZendeskToolExecutionError("Valid organization ID is required")
        
        params = validate_pagination_params(page, per_page)
        return await make_zendesk_request("GET", f"/organizations/{organization_id}/tickets.json", params=params)
    except Exception as e:
        logger.error(f"Error getting tickets for organization {organization_id}: {e}")
        raise

async def get_organization_users(
    organization_id: int,
    page: Optional[int] = None,
    per_page: Optional[int] = None
) -> Dict[str, Any]:
    """Get users for a specific organization."""
    try:
        if not organization_id or organization_id <= 0:
            raise ZendeskToolExecutionError("Valid organization ID is required")
        
        params = validate_pagination_params(page, per_page)
        return await make_zendesk_request("GET", f"/organizations/{organization_id}/users.json", params=params)
    except Exception as e:
        logger.error(f"Error getting users for organization {organization_id}: {e}")
        raise
