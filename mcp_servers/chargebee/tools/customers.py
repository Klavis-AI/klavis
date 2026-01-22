import logging
from typing import Any, Dict, Optional
from .base import make_request

# Configure logging
logger = logging.getLogger(__name__)


async def list_customers(
    limit: Optional[int] = None,
    offset: Optional[str] = None,
    email: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> Dict[str, Any]:
    """List all customers from Chargebee."""
    logger.info("Executing tool: list_customers")

    params = {}

    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    if email is not None:
        params["email[is]"] = email
    if first_name is not None:
        params["first_name[is]"] = first_name
    if last_name is not None:
        params["last_name[is]"] = last_name

    try:
        return await make_request("GET", "/customers", params=params if params else None)
    except Exception as e:
        logger.exception(f"Error executing tool list_customers: {e}")
        raise e


async def get_customer(customer_id: str) -> Dict[str, Any]:
    """Get detailed information for a specific customer from Chargebee."""
    logger.info(f"Executing tool: get_customer for customer_id={customer_id}")

    try:
        return await make_request("GET", f"/customers/{customer_id}")
    except Exception as e:
        logger.exception(f"Error executing tool get_customer: {e}")
        raise e


async def create_customer(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    company: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new customer in Chargebee."""
    logger.info("Executing tool: create_customer")

    data = {}

    if first_name is not None:
        data["first_name"] = first_name
    if last_name is not None:
        data["last_name"] = last_name
    if email is not None:
        data["email"] = email
    if phone is not None:
        data["phone"] = phone
    if company is not None:
        data["company"] = company

    try:
        return await make_request("POST", "/customers", data=data if data else None)
    except Exception as e:
        logger.exception(f"Error executing tool create_customer: {e}")
        raise e


async def update_customer(
    customer_id: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    company: Optional[str] = None,
) -> Dict[str, Any]:
    """Update an existing customer in Chargebee."""
    logger.info(f"Executing tool: update_customer for customer_id={customer_id}")

    data = {}

    if first_name is not None:
        data["first_name"] = first_name
    if last_name is not None:
        data["last_name"] = last_name
    if email is not None:
        data["email"] = email
    if phone is not None:
        data["phone"] = phone
    if company is not None:
        data["company"] = company

    try:
        return await make_request("POST", f"/customers/{customer_id}", data=data if data else None)
    except Exception as e:
        logger.exception(f"Error executing tool update_customer: {e}")
        raise e


async def delete_customer(customer_id: str) -> Dict[str, Any]:
    """Delete a customer from Chargebee."""
    logger.info(f"Executing tool: delete_customer for customer_id={customer_id}")

    try:
        return await make_request("POST", f"/customers/{customer_id}/delete")
    except Exception as e:
        logger.exception(f"Error executing tool delete_customer: {e}")
        raise e
