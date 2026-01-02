"""
HubSpot Tickets API tools with Klavis sanitization layer.

All responses are validated through Pydantic schemas.
All errors are sanitized to expose only HTTP status codes.
"""

import logging
import json
from hubspot.crm.tickets import SimplePublicObjectInputForCreate, SimplePublicObjectInput

from .base import get_hubspot_client, safe_api_call
from .schemas import (
    Ticket,
    TicketList,
    TicketProperties,
    CreateResult,
    UpdateResult,
    DeleteResult,
    normalize_ticket
)
from .errors import (
    KlavisError,
    ValidationError,
    sanitize_exception
)

# Configure logging
logger = logging.getLogger(__name__)


async def hubspot_get_tickets(limit: int = 10) -> TicketList:
    """
    Fetch a list of tickets from HubSpot.

    Parameters:
    - limit: Number of tickets to return

    Returns:
    - Klavis-normalized TicketList schema
    """
    client = get_hubspot_client()
    
    try:
        logger.info(f"Fetching up to {limit} tickets...")
        
        result = safe_api_call(
            client.crm.tickets.basic_api.get_page,
            resource_type="ticket",
            limit=limit
        )
        
        # Normalize response through Klavis schema
        tickets = []
        for raw_ticket in getattr(result, 'results', []) or []:
            tickets.append(normalize_ticket(raw_ticket))
        
        logger.info(f"Fetched {len(tickets)} tickets successfully.")
        return TicketList(
            tickets=tickets,
            total=len(tickets),
            has_more=bool(getattr(result, 'paging', None))
        )
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="ticket")


async def hubspot_get_ticket_by_id(ticket_id: str) -> Ticket:
    """
    Fetch a ticket by its ID.

    Parameters:
    - ticket_id: HubSpot ticket ID

    Returns:
    - Klavis-normalized Ticket schema
    """
    client = get_hubspot_client()
    
    try:
        logger.info(f"Fetching ticket ID: {ticket_id}...")
        
        result = safe_api_call(
            client.crm.tickets.basic_api.get_by_id,
            resource_type="ticket",
            resource_id=ticket_id,
            ticket_id=ticket_id
        )
        
        logger.info(f"Fetched ticket ID: {ticket_id} successfully.")
        return normalize_ticket(result)
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="ticket", resource_id=ticket_id)


async def hubspot_create_ticket(properties: str) -> CreateResult:
    """
    Create a new ticket.

    Parameters:
    - properties: JSON string of ticket properties

    Returns:
    - Klavis-normalized CreateResult schema
    """
    client = get_hubspot_client()
    
    try:
        logger.info("Creating new ticket...")
        
        # Parse and validate input
        try:
            props = json.loads(properties)
        except json.JSONDecodeError:
            raise ValidationError(resource_type="ticket")
        
        data = SimplePublicObjectInputForCreate(properties=props)
        result = safe_api_call(
            client.crm.tickets.basic_api.create,
            resource_type="ticket",
            simple_public_object_input_for_create=data
        )
        
        logger.info("Ticket created successfully.")
        return CreateResult(
            status="success",
            message="Ticket created successfully",
            resource_id=getattr(result, 'id', None)
        )
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="ticket")


async def hubspot_update_ticket_by_id(ticket_id: str, updates: str) -> UpdateResult:
    """
    Update a ticket by ID.

    Parameters:
    - ticket_id: HubSpot ticket ID
    - updates: JSON string of updated fields

    Returns:
    - Klavis-normalized UpdateResult schema
    """
    client = get_hubspot_client()
    
    try:
        logger.info(f"Updating ticket ID: {ticket_id}...")
        
        # Parse and validate input
        try:
            updates_dict = json.loads(updates)
        except json.JSONDecodeError:
            raise ValidationError(resource_type="ticket")
        
        data = SimplePublicObjectInput(properties=updates_dict)
        safe_api_call(
            client.crm.tickets.basic_api.update,
            resource_type="ticket",
            resource_id=ticket_id,
            ticket_id=ticket_id,
            simple_public_object_input=data
        )
        
        logger.info(f"Ticket ID: {ticket_id} updated successfully.")
        return UpdateResult(
            status="success",
            message="Ticket updated successfully",
            resource_id=ticket_id
        )
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="ticket", resource_id=ticket_id)


async def hubspot_delete_ticket_by_id(ticket_id: str) -> DeleteResult:
    """
    Delete a ticket by ID.

    Parameters:
    - ticket_id: HubSpot ticket ID

    Returns:
    - Klavis-normalized DeleteResult schema
    """
    client = get_hubspot_client()
    
    try:
        logger.info(f"Deleting ticket ID: {ticket_id}...")
        
        safe_api_call(
            client.crm.tickets.basic_api.archive,
            resource_type="ticket",
            resource_id=ticket_id,
            ticket_id=ticket_id
        )
        
        logger.info(f"Ticket ID: {ticket_id} deleted successfully.")
        return DeleteResult(
            status="success",
            message="Ticket deleted successfully",
            resource_id=ticket_id
        )
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="ticket", resource_id=ticket_id)
