import logging
from typing import Any, Dict, Optional, List
from .base import make_http_request

# Configure logging
logger = logging.getLogger(__name__)

async def search_persons(
    term: Optional[str] = None,
    page_size: int = 10,
    page_token: Optional[str] = None
) -> Dict[str, Any]:
    """Search for persons."""
    logger.info(f"Executing tool: search_persons with term: {term}")
    try:
        params = {
            "page_size": page_size
        }
        if term:
            params["term"] = term
        if page_token:
            params["page_token"] = page_token
        
        return await make_http_request("GET", "/persons", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool search_persons: {e}")
        raise e

async def get_person_by_id(person_id: int) -> Dict[str, Any]:
    """Get a specific person by ID."""
    logger.info(f"Executing tool: get_person_by_id with person_id: {person_id}")
    try:
        return await make_http_request("GET", f"/persons/{person_id}")
    except Exception as e:
        logger.exception(f"Error executing tool get_person_by_id: {e}")
        raise e

async def create_person(
    first_name: str,
    last_name: str,
    emails: Optional[List[str]] = None,
    organization_ids: Optional[List[int]] = None
) -> Dict[str, Any]:
    """Create a new person."""
    logger.info(f"Executing tool: create_person with name: {first_name} {last_name}")
    try:
        data = {
            "first_name": first_name,
            "last_name": last_name
        }
        if emails:
            data["emails"] = emails
        if organization_ids:
            data["organization_ids"] = organization_ids
        
        return await make_http_request("POST", "/persons", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool create_person: {e}")
        raise e

async def update_person(
    person_id: int,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    emails: Optional[List[str]] = None,
    organization_ids: Optional[List[int]] = None
) -> Dict[str, Any]:
    """Update an existing person."""
    logger.info(f"Executing tool: update_person with person_id: {person_id}")
    try:
        data = {}
        if first_name:
            data["first_name"] = first_name
        if last_name:
            data["last_name"] = last_name
        if emails:
            data["emails"] = emails
        if organization_ids:
            data["organization_ids"] = organization_ids
        
        return await make_http_request("PUT", f"/persons/{person_id}", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool update_person: {e}")
        raise e

async def delete_person(person_id: int) -> Dict[str, Any]:
    """Delete a person."""
    logger.info(f"Executing tool: delete_person with person_id: {person_id}")
    try:
        return await make_http_request("DELETE", f"/persons/{person_id}")
    except Exception as e:
        logger.exception(f"Error executing tool delete_person: {e}")
        raise e 