import logging
from typing import Any, Dict, Optional, List
from .base import make_request

# Configure logging
logger = logging.getLogger(__name__)

async def moneybird_list_contacts(
    administration_id: str,
    query: Optional[str] = None,
    page: Optional[int] = None
) -> Dict[str, Any]:
    """List all contacts in Moneybird."""
    logger.info("Executing tool: moneybird_list_contacts")
    
    params = {}
    if query:
        params["query"] = query
    if page:
        params["page"] = page
    
    try:
        return await make_request("GET", administration_id, "/contacts", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool moneybird_list_contacts: {e}")
        raise e

async def moneybird_get_contact(
    administration_id: str,
    contact_id: str
) -> Dict[str, Any]:
    """Get details for a specific contact by ID."""
    logger.info(f"Executing tool: moneybird_get_contact for contact_id: {contact_id}")
    
    try:
        return await make_request("GET", administration_id, f"/contacts/{contact_id}")
    except Exception as e:
        logger.exception(f"Error executing tool moneybird_get_contact: {e}")
        raise e

async def moneybird_create_contact(
    administration_id: str,
    contact_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a new company contact in Moneybird."""
    logger.info("Executing tool: moneybird_create_contact")
    
    try:
        return await make_request("POST", administration_id, "/contacts", data=contact_data)
    except Exception as e:
        logger.exception(f"Error executing tool moneybird_create_contact: {e}")
        raise e

async def moneybird_create_contact_person(
    administration_id: str,
    contact_id: str,
    contact_person_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a new contact person within an existing contact in Moneybird."""
    logger.info(f"Executing tool: moneybird_create_contact_person for contact_id: {contact_id}")
    
    try:
        return await make_request("POST", administration_id, f"/contacts/{contact_id}/contact_people", data=contact_person_data)
    except Exception as e:
        logger.exception(f"Error executing tool moneybird_create_contact_person: {e}")
        raise e