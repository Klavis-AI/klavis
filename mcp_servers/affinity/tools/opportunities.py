import logging
from typing import Any, Dict, Optional, List
from .base import make_v2_request

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

 