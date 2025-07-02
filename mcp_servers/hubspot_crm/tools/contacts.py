import logging
import json
from hubspot.crm.contacts import SimplePublicObjectInputForCreate, SimplePublicObjectInput
from .base import get_hubspot_client

# Configure logging
logger = logging.getLogger(__name__)

async def hubspot_get_contacts(limit: int = 10):
    """
    Fetch a list of contacts from HubSpot.

    Parameters:
    - limit: Number of contacts to retrieve

    Returns:
    - Paginated contacts response
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info(f"Fetching up to {limit} contacts from HubSpot")
        result = client.crm.contacts.basic_api.get_page(limit=limit)
        logger.info("Successfully fetched contacts")
        return result
    except Exception as e:
        logger.error(f"Error fetching contacts: {e}")
        raise e

async def hubspot_get_contact_by_id(contact_id: str):
    """
    Get a specific contact by ID.

    Parameters:
    - contact_id: ID of the contact to retrieve

    Returns:
    - Contact object
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info(f"Fetching contact with ID: {contact_id}")
        result = client.crm.contacts.basic_api.get_by_id(contact_id)
        logger.info("Successfully fetched contact")
        return result
    except Exception as e:
        logger.error(f"Error fetching contact by ID: {e}")
        raise e

async def hubspot_delete_contact_by_id(contact_id: str) -> str:
    """
    Delete a contact by ID.

    Parameters:
    - contact_id: ID of the contact to delete

    Returns:
    - Status message
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info(f"Deleting contact with ID: {contact_id}")
        client.crm.contacts.basic_api.archive(contact_id)
        logger.info("Successfully deleted contact")
        return "Deleted"
    except Exception as e:
        logger.error(f"Error deleting contact: {e}")
        raise e

async def hubspot_create_contact(properties: str) -> str:
    """
    Create a new contact using JSON string of properties.

    Parameters:
    - properties: JSON string containing contact fields

    Returns:
    - Status message
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        properties = json.loads(properties)
        logger.info(f"Creating contact with properties: {properties}")
        data = SimplePublicObjectInputForCreate(properties=properties)
        client.crm.contacts.basic_api.create(simple_public_object_input_for_create=data)
        logger.info("Successfully created contact")
        return "Created"
    except Exception as e:
        logger.error(f"Error creating contact: {e}")
        raise e

async def hubspot_update_contact_by_id(contact_id: str, updates: str) -> str:
    """
    Update a contact by ID.

    Parameters:
    - contact_id: ID of the contact to update
    - updates: JSON string of properties to update

    Returns:
    - Status message
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        updates = json.loads(updates)
        logger.info(f"Updating contact ID: {contact_id} with updates: {updates}")
        data = SimplePublicObjectInput(properties=updates)
        client.crm.contacts.basic_api.update(contact_id, data)
        logger.info("Successfully updated contact")
        return "Done"
    except Exception as e:
        logger.error(f"Update failed: {e}")
        return f"Error occurred: {e}"