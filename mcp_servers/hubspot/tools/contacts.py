"""
HubSpot Contacts API tools with Klavis sanitization layer.

All responses are validated through Pydantic schemas.
All errors are sanitized to expose only HTTP status codes.
"""

import logging
import json
from hubspot.crm.contacts import SimplePublicObjectInputForCreate, SimplePublicObjectInput

from .base import get_hubspot_client, safe_api_call
from .schemas import (
    Contact,
    ContactList,
    ContactProperties,
    CreateResult,
    UpdateResult,
    DeleteResult,
    normalize_contact
)
from .errors import (
    KlavisError,
    ValidationError,
    sanitize_exception,
    format_error_response
)

# Configure logging
logger = logging.getLogger(__name__)


async def hubspot_get_contacts(limit: int = 10) -> ContactList:
    """
    Fetch a list of contacts from HubSpot.

    Parameters:
    - limit: Number of contacts to retrieve

    Returns:
    - Klavis-normalized ContactList schema
    """
    client = get_hubspot_client()
    
    try:
        logger.info(f"Fetching up to {limit} contacts from HubSpot")
        
        # Make API call with error sanitization
        result = safe_api_call(
            client.crm.contacts.basic_api.get_page,
            resource_type="contact",
            limit=limit
        )
        
        # Normalize response through Klavis schema
        contacts = []
        for raw_contact in getattr(result, 'results', []) or []:
            contacts.append(normalize_contact(raw_contact))
        
        logger.info("Successfully fetched contacts")
        return ContactList(
            contacts=contacts,
            total=len(contacts),
            has_more=bool(getattr(result, 'paging', None))
        )
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="contact")


async def hubspot_get_contact_by_id(contact_id: str) -> Contact:
    """
    Get a specific contact by ID.

    Parameters:
    - contact_id: ID of the contact to retrieve

    Returns:
    - Klavis-normalized Contact schema
    """
    client = get_hubspot_client()
    
    try:
        logger.info(f"Fetching contact with ID: {contact_id}")
        
        result = safe_api_call(
            client.crm.contacts.basic_api.get_by_id,
            resource_type="contact",
            resource_id=contact_id,
            contact_id=contact_id
        )
        
        logger.info("Successfully fetched contact")
        return normalize_contact(result)
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="contact", resource_id=contact_id)


async def hubspot_delete_contact_by_id(contact_id: str) -> DeleteResult:
    """
    Delete a contact by ID.

    Parameters:
    - contact_id: ID of the contact to delete

    Returns:
    - Klavis-normalized DeleteResult schema
    """
    client = get_hubspot_client()
    
    try:
        logger.info(f"Deleting contact with ID: {contact_id}")
        
        safe_api_call(
            client.crm.contacts.basic_api.archive,
            resource_type="contact",
            resource_id=contact_id,
            contact_id=contact_id
        )
        
        logger.info("Successfully deleted contact")
        return DeleteResult(
            status="success",
            message="Contact deleted successfully",
            resource_id=contact_id
        )
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="contact", resource_id=contact_id)


async def hubspot_create_contact(properties: str) -> CreateResult:
    """
    Create a new contact using JSON string of properties.

    Parameters:
    - properties: JSON string containing contact fields

    Returns:
    - Klavis-normalized CreateResult schema
    """
    client = get_hubspot_client()
    
    try:
        # Parse and validate input
        try:
            properties_dict = json.loads(properties)
        except json.JSONDecodeError:
            raise ValidationError(resource_type="contact")
        
        # Common property name validation
        property_corrections = {
            'first_name': 'firstname',
            'last_name': 'lastname',
            'full_name': 'firstname',  # Needs to be split
            'mobile': 'mobilephone',
            'mobile_phone': 'mobilephone',
            'job_title': 'jobtitle',
            'postal_code': 'zip',
            'postalcode': 'zip',
            'zipcode': 'zip',
        }
        
        # Check for common mistakes
        invalid_props = []
        for prop_key in properties_dict.keys():
            if prop_key in property_corrections:
                invalid_props.append(prop_key)
        
        if invalid_props:
            raise ValidationError(resource_type="contact")
        
        logger.info(f"Creating contact")
        
        data = SimplePublicObjectInputForCreate(properties=properties_dict)
        result = safe_api_call(
            client.crm.contacts.basic_api.create,
            resource_type="contact",
            simple_public_object_input_for_create=data
        )
        
        logger.info("Successfully created contact")
        return CreateResult(
            status="success",
            message="Contact created successfully",
            resource_id=getattr(result, 'id', None)
        )
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="contact")


async def hubspot_update_contact_by_id(contact_id: str, updates: str) -> UpdateResult:
    """
    Update a contact by ID.

    Parameters:
    - contact_id: ID of the contact to update
    - updates: JSON string of properties to update

    Returns:
    - Klavis-normalized UpdateResult schema
    """
    client = get_hubspot_client()
    
    try:
        # Parse and validate input
        try:
            updates_dict = json.loads(updates)
        except json.JSONDecodeError:
            raise ValidationError(resource_type="contact")
        
        logger.info(f"Updating contact ID: {contact_id}")
        
        data = SimplePublicObjectInput(properties=updates_dict)
        safe_api_call(
            client.crm.contacts.basic_api.update,
            resource_type="contact",
            resource_id=contact_id,
            contact_id=contact_id,
            simple_public_object_input=data
        )
        
        logger.info("Successfully updated contact")
        return UpdateResult(
            status="success",
            message="Contact updated successfully",
            resource_id=contact_id
        )
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="contact", resource_id=contact_id)
