import logging
from typing import Any, Dict, Optional, List
from .base import make_v2_request, make_http_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_all_opportunities(
    cursor: Optional[str] = None,
    limit: Optional[int] = None,
    ids: Optional[List[int]] = None
) -> Dict[str, Any]:
    """Get all Opportunities in Affinity.
    
    Returns basic information but NOT field data on each Opportunity.
    To access field data on Opportunities, use the lists endpoints.
    
    Args:
        cursor: Cursor for pagination
        limit: Number of items per page (1-100, default 100)
        ids: Opportunity IDs to filter by
    """
    logger.info("Executing tool: get_all_opportunities")
    try:
        params = {}
        if cursor:
            params["cursor"] = cursor
        if limit:
            params["limit"] = limit
        if ids:
            params["ids"] = ids
            
        return await make_v2_request("GET", "/opportunities", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool get_all_opportunities: {e}")
        raise e

async def get_single_opportunity(opportunity_id: int) -> Dict[str, Any]:
    """Get a single Opportunity by ID.
    
    Returns basic information but NOT field data on the Opportunity.
    To access field data on Opportunities, use the lists endpoints.
    
    Args:
        opportunity_id: Opportunity ID
    """
    logger.info(f"Executing tool: get_single_opportunity with opportunity_id: {opportunity_id}")
    try:
        return await make_v2_request("GET", f"/opportunities/{opportunity_id}")
    except Exception as e:
        logger.exception(f"Error executing tool get_single_opportunity: {e}")
        raise e

async def search_opportunities(
    term: Optional[str] = None,
    page_size: Optional[int] = None,
    page_token: Optional[str] = None
) -> Dict[str, Any]:
    """Search for opportunities in Affinity.
    
    Searches your team's data and fetches all the opportunities that meet the search criteria.
    The search term can be part of an opportunity name.
    
    Args:
        term: A string used to search all the opportunities in your team's data
        page_size: How many results to return per page (Default is 500)
        page_token: Token from previous response required to retrieve the next page of results
    """
    logger.info("Executing tool: search_opportunities")
    try:
        params = {}
        if term:
            params["term"] = term
        if page_size:
            params["page_size"] = page_size
        if page_token:
            params["page_token"] = page_token
            
        return await make_http_request("GET", "/opportunities", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool search_opportunities: {e}")
        raise e

 