import logging
from typing import Any, Dict, Optional, List
from .base import make_v2_request, make_http_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_all_companies(
    cursor: Optional[str] = None,
    limit: Optional[int] = None,
    ids: Optional[List[int]] = None,
    field_ids: Optional[List[str]] = None,
    field_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Get all Companies in Affinity with basic information and field data.
    
    Args:
        cursor: Cursor for pagination
        limit: Number of items per page (1-100, default 100)
        ids: Company IDs to filter by
        field_ids: Field IDs for field data
        field_types: Field types (enriched, global, relationship-intelligence)
    """
    logger.info("Executing tool: get_all_companies")
    try:
        params = {}
        if cursor:
            params["cursor"] = cursor
        if limit:
            params["limit"] = limit
        if ids:
            params["ids"] = ids
        if field_ids:
            params["fieldIds"] = field_ids
        if field_types:
            params["fieldTypes"] = field_types
            
        return await make_v2_request("GET", "/companies", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool get_all_companies: {e}")
        raise e

async def get_single_company(
    company_id: int,
    field_ids: Optional[List[str]] = None,
    field_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Get a single Company by ID with basic information and field data.
    
    Args:
        company_id: Company ID
        field_ids: Field IDs for field data
        field_types: Field types (enriched, global, relationship-intelligence)
    """
    logger.info(f"Executing tool: get_single_company with company_id: {company_id}")
    try:
        params = {}
        if field_ids:
            params["fieldIds"] = field_ids
        if field_types:
            params["fieldTypes"] = field_types
            
        return await make_v2_request("GET", f"/companies/{company_id}", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool get_single_company: {e}")
        raise e

async def get_company_fields_metadata(
    cursor: Optional[str] = None,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """Get metadata on Company Fields.
    
    Args:
        cursor: Cursor for pagination
        limit: Number of items per page (1-100, default 100)
    """
    logger.info("Executing tool: get_company_fields_metadata")
    try:
        params = {}
        if cursor:
            params["cursor"] = cursor
        if limit:
            params["limit"] = limit
            
        return await make_v2_request("GET", "/companies/fields", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool get_company_fields_metadata: {e}")
        raise e

async def get_company_lists(
    company_id: int,
    cursor: Optional[str] = None,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """Get all Lists that contain the specified Company.
    
    Args:
        company_id: Company ID
        cursor: Cursor for pagination
        limit: Number of items per page (1-100, default 100)
    """
    logger.info(f"Executing tool: get_company_lists with company_id: {company_id}")
    try:
        params = {}
        if cursor:
            params["cursor"] = cursor
        if limit:
            params["limit"] = limit
            
        return await make_v2_request("GET", f"/companies/{company_id}/lists", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool get_company_lists: {e}")
        raise e

async def get_company_list_entries(
    company_id: int,
    cursor: Optional[str] = None,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """Get List Entries for a Company across all Lists with field data.
    
    Args:
        company_id: Company ID
        cursor: Cursor for pagination
        limit: Number of items per page (1-100, default 100)
    """
    logger.info(f"Executing tool: get_company_list_entries with company_id: {company_id}")
    try:
        params = {}
        if cursor:
            params["cursor"] = cursor
        if limit:
            params["limit"] = limit
            
        return await make_v2_request("GET", f"/companies/{company_id}/list-entries", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool get_company_list_entries: {e}")
        raise e

async def search_organizations(
    term: Optional[str] = None,
    with_interaction_dates: Optional[bool] = None,
    with_interaction_persons: Optional[bool] = None,
    with_opportunities: Optional[bool] = None,
    page_size: Optional[int] = None,
    page_token: Optional[str] = None
) -> Dict[str, Any]:
    """Search for organizations / companies in Affinity.
    
    Searches your team's data and fetches all the organizations that meet the search criteria.
    The search term can be part of an organization name or domain.
    
    Args:
        term: A string used to search all the organizations in your team's data
        with_interaction_dates: When true, interaction dates will be present on the returned resources
        with_interaction_persons: When true, persons for each interaction will be returned
        with_opportunities: When true, opportunity IDs will be returned for each organization
        page_size: How many results to return per page (Default is 500)
        page_token: Token from previous response required to retrieve the next page of results
    """
    logger.info("Executing tool: search_organizations")
    try:
        params = {}
        if term:
            params["term"] = term
        if with_interaction_dates is not None:
            params["with_interaction_dates"] = with_interaction_dates
        if with_interaction_persons is not None:
            params["with_interaction_persons"] = with_interaction_persons
        if with_opportunities is not None:
            params["with_opportunities"] = with_opportunities
        if page_size:
            params["page_size"] = page_size
        if page_token:
            params["page_token"] = page_token
            
        return await make_http_request("GET", "/organizations", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool search_organizations: {e}")
        raise e 