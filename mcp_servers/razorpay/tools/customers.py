from typing import Any, Dict, Optional, List
import logging

from .base import RazorpayClient
from .Constants import Version

logger = logging.getLogger(__name__)

version = Version.V1


async def create_customer(
    name: str,
    email: Optional[str] = None,
    contact: Optional[str] = None,
    gstin: Optional[str] = None,
    fail_existing: Optional[str] = None,
    notes: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Creates a new Razorpay Customer.

    Args:
        name (str): Customer's name (3-50 characters).
        email (Optional[str]): Customer's email address (max 64 chars).
        contact (Optional[str]): Customer's phone number (max 15 chars).
        gstin (Optional[str]): Customer's GST number.
        fail_existing (Optional[str]): '1' to error on duplicates, '0' to fetch.
        notes (Optional[Dict[str, Any]]): Key-value pairs for additional information.

    Returns:
        A dictionary containing customer details on success, or an error dictionary on failure.
    """
    # --- Input Validation ---
    if not isinstance(name, str) or not (3 <= len(name) <= 50):
        raise ValueError("Field 'name' is required and must be between 3 and 50 characters long.")

    payload = {"name": name}

    if email is not None:
        if not isinstance(email, str) or len(email) > 64:
            raise ValueError("Field 'email' must be a string and cannot exceed 64 characters.")
        payload["email"] = email

    if contact is not None:
        if not isinstance(contact, str) or len(contact) > 15:
            raise ValueError("Field 'contact' must be a string and cannot exceed 15 characters.")
        payload["contact"] = contact

    if gstin is not None:
        if not isinstance(gstin, str):
            raise ValueError("Field 'gstin' must be a string.")
        payload["gstin"] = gstin

    if fail_existing is not None:
        if fail_existing not in {'0', '1'}:
            raise ValueError("Field 'fail_existing' must be either '0' or '1'.")
        payload["fail_existing"] = fail_existing

    if notes is not None:
        if not isinstance(notes, dict) or len(notes) > 15:
            raise ValueError("Field 'notes' must be a dictionary with no more than 15 key-value pairs.")
        payload["notes"] = notes


    try:
        result = await RazorpayClient.make_request(
            method="POST",
            endpoint="/customers",
            data=payload,
            version=version
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception(f"Razorpay API call failed while creating customer: {e}")
        return {
            "success": False,
            "error": "An external API error occurred while creating a customer",
            "details": str(e),
        }


async def edit_customer_details(
    customer_id: str,
    name: Optional[str] = None,
    email: Optional[str] = None,
    contact: Optional[str] = None
) -> Dict[str, Any]:
    """
    Edits a customer's details by their ID.

    Args:
        customer_id (str): The unique ID of the customer to edit.
        name (Optional[str]): Customer's new name (3-50 characters).
        email (Optional[str]): Customer's new email address (max 64 chars).
        contact (Optional[str]): Customer's new phone number (max 15 chars).

    Returns:
        A dictionary containing the updated customer details or an error dictionary.
    """
    if not customer_id or not isinstance(customer_id, str):
        raise ValueError('Customer ID must be a non-empty string.')

    payload = {}
    if name is not None:
        if not isinstance(name, str) or not (3 <= len(name) <= 50):
            raise ValueError("Field 'name' must be between 3 and 50 characters.")
        payload['name'] = name
    
    if email is not None:
        if not isinstance(email, str) or len(email) > 64:
            raise ValueError("Field 'email' cannot exceed 64 characters.")
        payload['email'] = email
        
    if contact is not None:
        if not isinstance(contact, str) or len(contact) > 15:
            raise ValueError("Field 'contact' cannot exceed 15 characters.")
        payload['contact'] = contact
        
    if not payload:
        raise ValueError("At least one field (name, email, or contact) must be provided to update.")

    try:
        result = await RazorpayClient.make_request(
            method="PUT",
            endpoint=f"/customers/{customer_id}",
            data=payload,
            version=version
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception(f"Razorpay API call failed while updating customer: {e}")
        return {
            "success": False,
            "error": "An external API error occurred while updating customer",
            "details": str(e),
        }

async def fetch_all_customers(
    count:Optional[str] = None,
    skip:Optional[str]=None

)->Dict[str,Any]:
    
    """
    Use this endpoint to retrieve the details of all the customers.
    Args:
        count : The number of QR codes to fetch (default 10, max 100).
        skip : The number of QR codes to skip (for pagination).

    Returns:
        A dictionary containing the list of Customers on success,
        or an error dictionary on failure.

    """
    
    params={}
    if count is not None:
        if not isinstance(count, int) or not (1 <= count <= 100):
            raise ValueError("Parameter 'count' must be an integer between 1 and 100.")
        params["count"] = count

    if skip is not None:
        if not isinstance(skip, int) or skip < 0:
            raise ValueError("Parameter 'skip' must be a non-negative integer.")
        params["skip"] = skip

    
    try:
        result = await RazorpayClient.make_request(
            method="GET",
            endpoint="/customers",
            data=None,
            params=params,
            version=version
        )
        return {"success": True, "data": result}

    except Exception as e:
        logger.exception(f"Razorpay API call failed while fetching customers: {e}")
        return {
            "success": False,
            "error": "An external API error occurred while fetching customers",
            "details": str(e),
        }

async def fetch_customer_by_id(
        customer_id:str

)->Dict[str,Any]:
    """
    Use this endpoint to retrieve details of a customer with id.
    Args:
        customer_id:str
    Returns:
        Fetched Customer dictionary
    """

    if(not customer_id or not isinstance(customer_id,str)):
        raise ValueError('Customer id must be a non empty string')

    try:
        result = await RazorpayClient.make_request(
            method="GET",
            endpoint=f"/customers/{customer_id}",
            data=None,
            version=version
        )
        return {"success": True, "data": result}

    except Exception as e:
        logger.exception(f"Razorpay API call failed while fetching customerby id: {e}")
        return {
            "success": False,
            "error": "An external API error occurred while fetching customer by id",
            "details": str(e),
        }
