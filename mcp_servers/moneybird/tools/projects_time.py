import logging
from typing import Any, Dict, Optional
from .base import make_request

# Configure logging
logger = logging.getLogger(__name__)

async def moneybird_list_projects(
    administration_id: str,
    state: Optional[str] = None,
    page: Optional[int] = None
) -> Dict[str, Any]:
    """List all projects in Moneybird."""
    logger.info("Executing tool: moneybird_list_projects")
    
    params = {}
    if state:
        params["state"] = state  # active, archived, all
    if page:
        params["page"] = page
    
    try:
        return await make_request("GET", administration_id, "/projects", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool moneybird_list_projects: {e}")
        raise e

async def moneybird_list_time_entries(
    administration_id: str,
    period: Optional[str] = None,
    contact_id: Optional[str] = None,
    project_id: Optional[str] = None,
    user_id: Optional[str] = None,
    page: Optional[int] = None
) -> Dict[str, Any]:
    """List all time entries in Moneybird."""
    logger.info("Executing tool: moneybird_list_time_entries")
    
    params = {}
    if period:
        params["period"] = period
    if contact_id:
        params["contact_id"] = contact_id
    if project_id:
        params["project_id"] = project_id
    if user_id:
        params["user_id"] = user_id
    if page:
        params["page"] = page
    
    try:
        return await make_request("GET", administration_id, "/time_entries", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool moneybird_list_time_entries: {e}")
        raise e