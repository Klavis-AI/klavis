from typing import Dict, List, Optional, Any
from .base import make_freshdesk_request, handle_freshdesk_error, remove_none_values
import logging

logger = logging.getLogger(__name__)

async def create_company(
    name: str,
    domains: Optional[List[str]] = None,
    description: Optional[str] = None,
    note: Optional[str] = None,
    health_score: Optional[str] = None,
    account_tier: Optional[str] = None,
    renewal_date: Optional[str] = None,
    industry: Optional[str] = None,
    custom_fields: Optional[Dict[str, Any]] = None,
    lookup_parameter: str = "display_id"
) -> Dict[str, Any]:
    """
    Create a new company in Freshdesk.
    
    Args:
        name: Name of the company (required, unique)
        domains: List of company domains
        description: Description of the company
        note: Any specific note about the company
        health_score: Health score of the company (e.g., "Happy", "At risk")
        account_tier: Account tier (e.g., "Basic", "Premium")
        renewal_date: Contract renewal date (YYYY-MM-DD)
        industry: Industry the company serves in
        custom_fields: Dictionary of custom field values
        lookup_parameter: Either "display_id" or "primary_field_value"
        
    Returns:
        Dictionary containing the created company details
    """
    try:

        company_data = {
            "name": name,
            "domains": domains or [],
            "description": description,
            "note": note,
            "health_score": health_score,
            "account_tier": account_tier,
            "renewal_date": renewal_date,
            "industry": industry,
            "custom_fields": custom_fields or {},
            "lookup_parameter": lookup_parameter
        }
        
        company_data = remove_none_values(company_data)
        
        response = await make_freshdesk_request("POST", "/companies", data=company_data)
        return response
        
    except Exception as e:
        return handle_freshdesk_error(e, "create", "company")

async def get_company_by_id(company_id: int) -> Dict[str, Any]:
    """
    Retrieve a company by ID.
    
    Args:
        company_id: ID of the company to retrieve
        
    Returns:
        Dictionary containing company details
    """
    try:
        response = await make_freshdesk_request("GET", f"/companies/{company_id}")
        return response
    except Exception as e:
        return handle_freshdesk_error(e, "retrieve", "company")

async def list_companies(
    updated_since: Optional[str] = None,
    page: int = 1,
    per_page: int = 30
) -> Dict[str, Any]:
    """
    List all companies with optional filtering.
    
    Args:
        updated_since: Filter companies updated since this date (ISO 8601 format)
        page: Page number (1-based)
        per_page: Number of records per page (max 100)
        
    Returns:
        Dictionary containing list of companies and pagination info
    """
    try:
        params = {
            "updated_since": updated_since,
            "page": page,
            "per_page": min(per_page, 100) 
        }
        
        params = remove_none_values(params)
        
        response = await make_freshdesk_request(
            "GET",
            "/companies",
            options={"query_params": params}
        )
        return response
        
    except Exception as e:
        return handle_freshdesk_error(e, "list", "companies")

async def filter_companies(
    query: str,
    page: int = 1,
    per_page: int = 30
) -> Dict[str, Any]:
    """
    Filter companies using a query string.
    
    Args:
        query: Search query (supports domain, custom fields, etc.)
        page: Page number (1-based)
        per_page: Number of records per page
        
    Returns:
        Dictionary containing search results and pagination info
    """
    try:
        params = {
            "query": f'"{query}"',
            "page": page,
            "per_page": min(per_page, 30)
        }
        
        response = await make_freshdesk_request(
            "GET",
            "/search/companies",
            options={"query_params": params}
        )
        return response
        
    except Exception as e:
        return handle_freshdesk_error(e, "search", "companies")

async def update_company(
    company_id: int,
    name: Optional[str] = None,
    domains: Optional[List[str]] = None,
    description: Optional[str] = None,
    note: Optional[str] = None,
    health_score: Optional[str] = None,
    account_tier: Optional[str] = None,
    renewal_date: Optional[str] = None,
    industry: Optional[str] = None,
    custom_fields: Optional[Dict[str, Any]] = None,
    lookup_parameter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update an existing company.
    
    Args:
        company_id: ID of the company to update
        name: New name for the company
        domains: List of domains (will replace existing domains if provided)
        description: New description
        note: New note
        health_score: Updated health score
        account_tier: Updated account tier
        renewal_date: New renewal date (YYYY-MM-DD)
        industry: Updated industry
        custom_fields: Dictionary of custom field values to update
        lookup_parameter: Either "display_id" or "primary_field_value"
        
    Returns:
        Dictionary containing the updated company details
    """
    try:
        update_data = {
            "name": name,
            "domains": domains,
            "description": description,
            "note": note,
            "health_score": health_score,
            "account_tier": account_tier,
            "renewal_date": renewal_date,
            "industry": industry,
            "custom_fields": custom_fields,
            "lookup_parameter": lookup_parameter
        }
        
        update_data = remove_none_values(update_data)
        
        if not update_data:
            raise ValueError("No fields to update")
            
        response = await make_freshdesk_request(
            "PUT",
            f"/companies/{company_id}",
            data=update_data
        )
        return response
        
    except Exception as e:
        return handle_freshdesk_error(e, "update", "company")

async def delete_company(company_id: int) -> Dict[str, Any]:
    """
    Delete a company.
    
    Note: This only deletes the company record, not the associated contacts.
    
    Args:
        company_id: ID of the company to delete
        
    Returns:
        Dictionary indicating success or failure
    """
    try:
        await make_freshdesk_request("DELETE", f"/companies/{company_id}")
        return {"success": True, "message": f"Company {company_id} deleted successfully"}
    except Exception as e:
        return handle_freshdesk_error(e, "delete", "company")

async def search_companies_by_name(name: str) -> Dict[str, Any]:
    """
    Search for companies by name (autocomplete).
    
    Args:
        name: Search name (case-insensitive)
        
    Returns:
        Dictionary containing matching companies
    """
    try:
        response = await make_freshdesk_request(
            "GET",
            "/companies/autocomplete",
            options={"query_params": {"name": name}}
        )
        return response
    except Exception as e:
        return handle_freshdesk_error(e, "search", "companies")