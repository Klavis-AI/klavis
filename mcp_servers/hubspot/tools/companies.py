"""
HubSpot Companies API tools with Klavis sanitization layer.

All responses are validated through Pydantic schemas.
All errors are sanitized to expose only HTTP status codes.
"""

import logging
import json
from hubspot.crm.companies import SimplePublicObjectInputForCreate, SimplePublicObjectInput

from .base import get_hubspot_client, safe_api_call
from .schemas import (
    Company,
    CompanyList,
    CompanyProperties,
    CreateResult,
    UpdateResult,
    DeleteResult,
    normalize_company
)
from .errors import (
    KlavisError,
    ValidationError,
    sanitize_exception
)

# Configure logging
logger = logging.getLogger(__name__)


async def hubspot_create_companies(properties: str) -> CreateResult:
    """
    Create a new company using JSON string of properties.

    Parameters:
    - properties: JSON string of company fields

    Returns:
    - Klavis-normalized CreateResult schema
    """
    client = get_hubspot_client()
    
    try:
        logger.info("Creating company...")
        
        # Parse and validate input
        try:
            properties_dict = json.loads(properties)
        except json.JSONDecodeError:
            raise ValidationError(resource_type="company")
        
        # Common property name validation
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
        
        # Check for common mistakes
        invalid_props = []
        for prop_key in properties_dict.keys():
            if prop_key in property_corrections:
                invalid_props.append(prop_key)
        
        if invalid_props:
            raise ValidationError(resource_type="company")
        
        data = SimplePublicObjectInputForCreate(properties=properties_dict)
        result = safe_api_call(
            client.crm.companies.basic_api.create,
            resource_type="company",
            simple_public_object_input_for_create=data
        )
        
        logger.info("Company created successfully.")
        return CreateResult(
            status="success",
            message="Company created successfully",
            resource_id=getattr(result, 'id', None)
        )
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="company")


async def hubspot_get_companies(limit: int = 10) -> CompanyList:
    """
    Fetch a list of companies from HubSpot.

    Parameters:
    - limit: Number of companies to retrieve

    Returns:
    - Klavis-normalized CompanyList schema
    """
    client = get_hubspot_client()
    
    try:
        logger.info(f"Fetching up to {limit} companies...")
        
        result = safe_api_call(
            client.crm.companies.basic_api.get_page,
            resource_type="company",
            limit=limit
        )
        
        # Normalize response through Klavis schema
        companies = []
        for raw_company in getattr(result, 'results', []) or []:
            companies.append(normalize_company(raw_company))
        
        logger.info(f"Fetched {len(companies)} companies successfully.")
        return CompanyList(
            companies=companies,
            total=len(companies),
            has_more=bool(getattr(result, 'paging', None))
        )
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="company")


async def hubspot_get_company_by_id(company_id: str) -> Company:
    """
    Get a company by ID.

    Parameters:
    - company_id: ID of the company

    Returns:
    - Klavis-normalized Company schema
    """
    client = get_hubspot_client()
    
    try:
        logger.info(f"Fetching company with ID: {company_id}...")
        
        result = safe_api_call(
            client.crm.companies.basic_api.get_by_id,
            resource_type="company",
            resource_id=company_id,
            company_id=company_id
        )
        
        logger.info(f"Fetched company ID: {company_id} successfully.")
        return normalize_company(result)
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="company", resource_id=company_id)


async def hubspot_update_company_by_id(company_id: str, updates: str) -> UpdateResult:
    """
    Update a company by ID.

    Parameters:
    - company_id: ID of the company to update
    - updates: JSON string of property updates

    Returns:
    - Klavis-normalized UpdateResult schema
    """
    client = get_hubspot_client()
    
    try:
        logger.info(f"Updating company ID: {company_id}...")
        
        # Parse and validate input
        try:
            updates_dict = json.loads(updates)
        except json.JSONDecodeError:
            raise ValidationError(resource_type="company")
        
        update = SimplePublicObjectInput(properties=updates_dict)
        safe_api_call(
            client.crm.companies.basic_api.update,
            resource_type="company",
            resource_id=company_id,
            company_id=company_id,
            simple_public_object_input=update
        )
        
        logger.info(f"Company ID: {company_id} updated successfully.")
        return UpdateResult(
            status="success",
            message="Company updated successfully",
            resource_id=company_id
        )
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="company", resource_id=company_id)


async def hubspot_delete_company_by_id(company_id: str) -> DeleteResult:
    """
    Delete a company by ID.

    Parameters:
    - company_id: ID of the company

    Returns:
    - Klavis-normalized DeleteResult schema
    """
    client = get_hubspot_client()
    
    try:
        logger.info(f"Deleting company ID: {company_id}...")
        
        safe_api_call(
            client.crm.companies.basic_api.archive,
            resource_type="company",
            resource_id=company_id,
            company_id=company_id
        )
        
        logger.info(f"Company ID: {company_id} deleted successfully.")
        return DeleteResult(
            status="success",
            message="Company deleted successfully",
            resource_id=company_id
        )
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="company", resource_id=company_id)
