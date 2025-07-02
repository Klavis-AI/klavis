import logging
import json
from hubspot.crm.deals import SimplePublicObjectInputForCreate, SimplePublicObjectInput
from .base import get_hubspot_client

# Configure logging
logger = logging.getLogger(__name__)

async def hubspot_get_deals(limit: int = 10):
    """
    Fetch a list of deals from HubSpot.

    Parameters:
    - limit: Number of deals to return

    Returns:
    - List of deal records
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info(f"Fetching up to {limit} deals...")
        result = client.crm.deals.basic_api.get_page(limit=limit)
        logger.info(f"Fetched {len(result.results)} deals successfully.")
        return result
    except Exception as e:
        logger.error(f"Error fetching deals: {e}")
        return None

async def hubspot_get_deal_by_id(deal_id: str):
    """
    Fetch a deal by its ID.

    Parameters:
    - deal_id: HubSpot deal ID

    Returns:
    - Deal object
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info(f"Fetching deal ID: {deal_id}...")
        result = client.crm.deals.basic_api.get_by_id(deal_id)
        logger.info(f"Fetched deal ID: {deal_id} successfully.")
        return result
    except Exception as e:
        logger.error(f"Error fetching deal by ID: {e}")
        return None

async def hubspot_create_deal(properties: str):
    """
    Create a new deal.

    Parameters:
    - properties: JSON string of deal properties

    Returns:
    - Newly created deal
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info("Creating a new deal...")
        props = json.loads(properties)
        data = SimplePublicObjectInputForCreate(properties=props)
        result = client.crm.deals.basic_api.create(simple_public_object_input_for_create=data)
        logger.info("Deal created successfully.")
        return result
    except Exception as e:
        logger.error(f"Error creating deal: {e}")
        return f"Error occurred: {e}"

async def hubspot_update_deal_by_id(deal_id: str, updates: str):
    """
    Update a deal by ID.

    Parameters:
    - deal_id: HubSpot deal ID
    - updates: JSON string of updated fields

    Returns:
    - "Done" on success, error message otherwise
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info(f"Updating deal ID: {deal_id}...")
        data = SimplePublicObjectInput(properties=json.loads(updates))
        client.crm.deals.basic_api.update(deal_id, data)
        logger.info(f"Deal ID: {deal_id} updated successfully.")
        return "Done"
    except Exception as e:
        logger.error(f"Update failed for deal ID {deal_id}: {e}")
        return f"Error occurred: {e}"

async def hubspot_delete_deal_by_id(deal_id: str):
    """
    Delete a deal by ID.

    Parameters:
    - deal_id: HubSpot deal ID

    Returns:
    - None
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info(f"Deleting deal ID: {deal_id}...")
        client.crm.deals.basic_api.archive(deal_id)
        logger.info(f"Deal ID: {deal_id} deleted successfully.")
        return "Deleted"
    except Exception as e:
        logger.error(f"Error deleting deal: {e}")
        return f"Error occurred: {e}"