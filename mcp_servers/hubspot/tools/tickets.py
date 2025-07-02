import logging
import json
from hubspot.crm.tickets import SimplePublicObjectInputForCreate, SimplePublicObjectInput
from .base import get_hubspot_client

# Configure logging
logger = logging.getLogger(__name__)

async def hubspot_get_tickets(limit: int = 10):
    """
    Fetch a list of tickets from HubSpot.

    Parameters:
    - limit: Number of tickets to return

    Returns:
    - List of ticket records
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info(f"Fetching up to {limit} tickets...")
        result = client.crm.tickets.basic_api.get_page(limit=limit)
        logger.info(f"Fetched {len(result.results)} tickets successfully.")
        return result
    except Exception as e:
        logger.error(f"Error fetching tickets: {e}")
        return None

async def hubspot_get_ticket_by_id(ticket_id: str):
    """
    Fetch a ticket by its ID.

    Parameters:
    - ticket_id: HubSpot ticket ID

    Returns:
    - Ticket object
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info(f"Fetching ticket ID: {ticket_id}...")
        result = client.crm.tickets.basic_api.get_by_id(ticket_id)
        logger.info(f"Fetched ticket ID: {ticket_id} successfully.")
        return result
    except Exception as e:
        logger.error(f"Error fetching ticket by ID: {e}")
        return None

async def hubspot_create_ticket(properties: str):
    """
    Create a new ticket.

    Parameters:
    - properties: JSON string of ticket properties

    Returns:
    - Newly created ticket
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info("Creating new ticket...")
        props = json.loads(properties)
        data = SimplePublicObjectInputForCreate(properties=props)
        result = client.crm.tickets.basic_api.create(simple_public_object_input_for_create=data)
        logger.info("Ticket created successfully.")
        return result
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        return f"Error occurred: {e}"

async def hubspot_update_ticket_by_id(ticket_id: str, updates: str):
    """
    Update a ticket by ID.

    Parameters:
    - ticket_id: HubSpot ticket ID
    - updates: JSON string of updated fields

    Returns:
    - "Done" on success, error message otherwise
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info(f"Updating ticket ID: {ticket_id}...")
        data = SimplePublicObjectInput(properties=json.loads(updates))
        client.crm.tickets.basic_api.update(ticket_id, data)
        logger.info(f"Ticket ID: {ticket_id} updated successfully.")
        return "Done"
    except Exception as e:
        logger.error(f"Update failed for ticket ID {ticket_id}: {e}")
        return f"Error occurred: {e}"

async def hubspot_delete_ticket_by_id(ticket_id: str):
    """
    Delete a ticket by ID.

    Parameters:
    - ticket_id: HubSpot ticket ID

    Returns:
    - None
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info(f"Deleting ticket ID: {ticket_id}...")
        client.crm.tickets.basic_api.archive(ticket_id)
        logger.info(f"Ticket ID: {ticket_id} deleted successfully.")
        return "Deleted"
    except Exception as e:
        logger.error(f"Error deleting ticket ID {ticket_id}: {e}")
        return f"Error occurred: {e}"