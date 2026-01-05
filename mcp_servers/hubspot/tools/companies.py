import logging
import json
from typing import Dict, Any
from hubspot.crm.companies import SimplePublicObjectInputForCreate, SimplePublicObjectInput
from .base import get_hubspot_client, normalize_company

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
        properties_dict = json.loads(properties)
        
        # Common property name mistakes mapping
        property_corrections = {
            'postal_code': 'zip',
            'postalcode': 'zip',
            'zipcode': 'zip',
            'num_of_employees': 'numberofemployees',
            'num_employees': 'numberofemployees',
            'employee_count': 'numberofemployees',
            'employees': 'numberofemployees',
            'company_name': 'name',
            'annual_revenue': 'annualrevenue',
            'web_site': 'website',
            'url': 'website',
        }
        
        # Check for common mistakes and provide helpful suggestions
        suggestions = []
        for prop_key in properties_dict.keys():
            if prop_key in property_corrections:
                suggestions.append(
                    f"Property '{prop_key}' should be '{property_corrections[prop_key]}'"
                )
        
        if suggestions:
            error_msg = "Invalid property names detected:\n" + "\n".join(suggestions)
            error_msg += "\n\nTip: Call 'hubspot_list_properties' with object_type='companies' to see all valid property names."
            logger.warning(error_msg)
            return f"Error: {error_msg}"
        
        data = SimplePublicObjectInputForCreate(properties=properties_dict)
        client.crm.companies.basic_api.create(simple_public_object_input_for_create=data)
        logger.info("Company created successfully.")
        return "Created"
    except Exception as e:
        logger.error(f"Error creating company: {e}")
        return f"Error occurred: {e}"

async def hubspot_get_companies(limit: int = 10) -> Dict[str, Any]:
    """
    Fetch a list of companies from HubSpot.

    Parameters:
    - limit: Number of companies to retrieve

    Returns:
    - Normalized companies response
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info(f"Fetching up to {limit} companies...")
        result = client.crm.companies.basic_api.get_page(limit=limit)
        
        # Normalize response
        companies = [normalize_company(obj) for obj in (result.results or [])]
        
        logger.info(f"Fetched {len(companies)} companies successfully.")
        return {
            "count": len(companies),
            "companies": companies,
            "hasMore": result.paging.next.after is not None if result.paging and result.paging.next else False,
        }
    except Exception as e:
        logger.error(f"Error fetching companies: {e}")
        raise e


async def hubspot_get_company_by_id(company_id: str) -> Dict[str, Any]:
    """
    Get a company by ID.

    Parameters:
    - company_id: ID of the company

    Returns:
    - Normalized company object
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info(f"Fetching company with ID: {company_id}...")
        result = client.crm.companies.basic_api.get_by_id(company_id)
        
        # Normalize response
        company = normalize_company(result)
        
        logger.info(f"Fetched company ID: {company_id} successfully.")
        return {"company": company}
    except Exception as e:
        logger.error(f"Error fetching company by ID: {e}")
        raise e

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