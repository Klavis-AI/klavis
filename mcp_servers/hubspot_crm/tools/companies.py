import logging
import json
from hubspot.crm.companies import SimplePublicObjectInputForCreate, SimplePublicObjectInput
from .base import get_hubspot_client

# Configure logging
logger = logging.getLogger(__name__)

async def hubspot_create_companies(properties: str) -> str:
    """
    Create a new company using JSON string of properties.

    Parameters:
    - properties: JSON string of company fields

    Returns:
    - Status message
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info("Creating company...")
        properties = json.loads(properties)
        data = SimplePublicObjectInputForCreate(properties=properties)
        client.crm.companies.basic_api.create(simple_public_object_input_for_create=data)
        logger.info("Company created successfully.")
        return "Created"
    except Exception as e:
        logger.error(f"Error creating company: {e}")
        return f"Error occurred: {e}"

async def hubspot_get_companies(limit: int = 10):
    """
    Fetch a list of companies from HubSpot.

    Parameters:
    - limit: Number of companies to retrieve

    Returns:
    - Paginated companies response
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info(f"Fetching up to {limit} companies...")
        result = client.crm.companies.basic_api.get_page(limit=limit)
        logger.info(f"Fetched {len(result.results)} companies successfully.")
        return result
    except Exception as e:
        logger.error(f"Error fetching companies: {e}")
        return None

async def hubspot_get_company_by_id(company_id: str):
    """
    Get a company by ID.

    Parameters:
    - company_id: ID of the company

    Returns:
    - Company object
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info(f"Fetching company with ID: {company_id}...")
        result = client.crm.companies.basic_api.get_by_id(company_id)
        logger.info(f"Fetched company ID: {company_id} successfully.")
        return result
    except Exception as e:
        logger.error(f"Error fetching company by ID: {e}")
        return None

async def hubspot_update_company_by_id(company_id: str, updates: str) -> str:
    """
    Update a company by ID.

    Parameters:
    - company_id: ID of the company to update
    - updates: JSON string of property updates

    Returns:
    - Status message
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info(f"Updating company ID: {company_id}...")
        updates = json.loads(updates)
        update = SimplePublicObjectInput(properties=updates)
        client.crm.companies.basic_api.update(company_id, update)
        logger.info(f"Company ID: {company_id} updated successfully.")
        return "Done"
    except Exception as e:
        logger.error(f"Update failed: {e}")
        return f"Error occurred: {e}"

async def hubspot_delete_company_by_id(company_id: str) -> str:
    """
    Delete a company by ID.

    Parameters:
    - company_id: ID of the company

    Returns:
    - Status message
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info(f"Deleting company ID: {company_id}...")
        client.crm.companies.basic_api.archive(company_id)
        logger.info(f"Company ID: {company_id} deleted successfully.")
        return "Deleted"
    except Exception as e:
        logger.error(f"Error deleting company: {e}")
        return f"Error occurred: {e}"