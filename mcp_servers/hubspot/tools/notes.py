import logging
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from hubspot.crm.objects import SimplePublicObjectInputForCreate
from .base import get_hubspot_client

# Configure logging
logger = logging.getLogger(__name__)

async def hubspot_create_note(
    note_body: str,
    contact_ids: Optional[List[str]] = None,
    company_ids: Optional[List[str]] = None,
    deal_ids: Optional[List[str]] = None,
    ticket_ids: Optional[List[str]] = None,
    owner_id: Optional[str] = None,
    timestamp: Optional[str] = None
) -> str:
    """
    Create a new note in HubSpot.

    Parameters:
    - note_body: The content of the note
    - contact_ids: List of contact IDs to associate with the note
    - company_ids: List of company IDs to associate with the note
    - deal_ids: List of deal IDs to associate with the note
    - ticket_ids: List of ticket IDs to associate with the note
    - owner_id: HubSpot user ID of the note owner
    - timestamp: ISO 8601 timestamp or milliseconds since epoch for when the note was created (defaults to current time if not provided)

    Returns:
    - Status message with note ID
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        # Prepare the note properties
        properties = {
            "hs_note_body": note_body
        }
        
        # Add optional properties if provided
        if owner_id:
            properties["hubspot_owner_id"] = owner_id
        
        # hs_timestamp is required - use provided timestamp or current time
        if timestamp:
            properties["hs_timestamp"] = timestamp
        else:
            # Use current timestamp in milliseconds (HubSpot format)
            current_timestamp = int(datetime.now().timestamp() * 1000)
            properties["hs_timestamp"] = str(current_timestamp)
        
        # Prepare associations
        associations = []
        
        # Add contact associations
        if contact_ids:
            for contact_id in contact_ids:
                associations.append({
                    "to": {"id": contact_id},
                    "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 202}]
                })
        
        # Add company associations
        if company_ids:
            for company_id in company_ids:
                associations.append({
                    "to": {"id": company_id},
                    "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 190}]
                })
        
        # Add deal associations
        if deal_ids:
            for deal_id in deal_ids:
                associations.append({
                    "to": {"id": deal_id},
                    "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 214}]
                })
        
        # Add ticket associations
        if ticket_ids:
            for ticket_id in ticket_ids:
                associations.append({
                    "to": {"id": ticket_id},
                    "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 216}]
                })
        
        logger.info(f"Creating note with properties: {properties}")
        
        # Create the note using the objects API, Convert to HubSpot SDK format
        note_input = SimplePublicObjectInputForCreate(
            properties=properties,
            associations=associations if associations else None
        )
        
        result = client.crm.objects.notes.basic_api.create(
            simple_public_object_input_for_create=note_input
        )
        
        logger.info(f"Successfully created note with ID: {result.id}")
        return f"Note created successfully with ID: {result.id}"
        
    except Exception as e:
        logger.error(f"Error creating note: {e}")
        raise e 