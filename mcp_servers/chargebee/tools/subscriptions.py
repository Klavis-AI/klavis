import logging
from typing import Any, Dict, Optional
from .base import make_request

# Configure logging
logger = logging.getLogger(__name__)


async def list_subscriptions(
    limit: Optional[int] = None,
    offset: Optional[str] = None,
    customer_id: Optional[str] = None,
    plan_id: Optional[str] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """List all subscriptions from Chargebee with optional filters."""
    logger.info("Executing tool: list_subscriptions")

    params = {}

    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    if customer_id is not None:
        params["customer_id[is]"] = customer_id
    if plan_id is not None:
        params["plan_id[is]"] = plan_id
    if status is not None:
        params["status[is]"] = status

    try:
        return await make_request("GET", "/subscriptions", params=params if params else None)
    except Exception as e:
        logger.exception(f"Error executing tool list_subscriptions: {e}")
        raise e


async def get_subscription(subscription_id: str) -> Dict[str, Any]:
    """Get detailed information for a specific subscription from Chargebee."""
    logger.info(f"Executing tool: get_subscription for subscription_id={subscription_id}")

    try:
        return await make_request("GET", f"/subscriptions/{subscription_id}")
    except Exception as e:
        logger.exception(f"Error executing tool get_subscription: {e}")
        raise e


async def create_subscription(
    customer_id: str,
    item_price_id: str,
    quantity: Optional[int] = None,
    start_date: Optional[int] = None,
    trial_end: Optional[int] = None,
    billing_cycles: Optional[int] = None,
    auto_collection: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new subscription for a customer in Chargebee (Product Catalog 2.0)."""
    logger.info(f"Executing tool: create_subscription for customer_id={customer_id}")

    data = {
        "subscription_items[item_price_id][0]": item_price_id,
    }

    if quantity is not None:
        data["subscription_items[quantity][0]"] = quantity
    if start_date is not None:
        data["start_date"] = start_date
    if trial_end is not None:
        data["trial_end"] = trial_end
    if billing_cycles is not None:
        data["subscription_items[billing_cycles][0]"] = billing_cycles
    if auto_collection is not None:
        data["auto_collection"] = auto_collection

    try:
        return await make_request("POST", f"/customers/{customer_id}/subscription_for_items", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool create_subscription: {e}")
        raise e


async def update_subscription(
    subscription_id: str,
    item_price_id: Optional[str] = None,
    quantity: Optional[int] = None,
    start_date: Optional[int] = None,
    trial_end: Optional[int] = None,
    billing_cycles: Optional[int] = None,
    auto_collection: Optional[str] = None,
    po_number: Optional[str] = None,
) -> Dict[str, Any]:
    """Update an existing subscription in Chargebee (Product Catalog 2.0)."""
    logger.info(f"Executing tool: update_subscription for subscription_id={subscription_id}")

    data = {}

    if item_price_id is not None:
        data["subscription_items[item_price_id][0]"] = item_price_id
    if quantity is not None:
        data["subscription_items[quantity][0]"] = quantity
    if start_date is not None:
        data["start_date"] = start_date
    if trial_end is not None:
        data["trial_end"] = trial_end
    if billing_cycles is not None:
        data["subscription_items[billing_cycles][0]"] = billing_cycles
    if auto_collection is not None:
        data["auto_collection"] = auto_collection
    if po_number is not None:
        data["po_number"] = po_number

    try:
        return await make_request("POST", f"/subscriptions/{subscription_id}/update_for_items", data=data if data else None)
    except Exception as e:
        logger.exception(f"Error executing tool update_subscription: {e}")
        raise e


async def cancel_subscription(
    subscription_id: str,
    end_of_term: Optional[bool] = None,
    cancel_at: Optional[int] = None,
    credit_option_for_current_term_charges: Optional[str] = None,
    unbilled_charges_option: Optional[str] = None,
    cancel_reason_code: Optional[str] = None,
) -> Dict[str, Any]:
    """Cancel a subscription in Chargebee."""
    logger.info(f"Executing tool: cancel_subscription for subscription_id={subscription_id}")

    data = {}

    if end_of_term is not None:
        data["end_of_term"] = str(end_of_term).lower()
    if cancel_at is not None:
        data["cancel_at"] = cancel_at
    if credit_option_for_current_term_charges is not None:
        data["credit_option_for_current_term_charges"] = credit_option_for_current_term_charges
    if unbilled_charges_option is not None:
        data["unbilled_charges_option"] = unbilled_charges_option
    if cancel_reason_code is not None:
        data["cancel_reason_code"] = cancel_reason_code

    try:
        return await make_request("POST", f"/subscriptions/{subscription_id}/cancel_for_items", data=data if data else None)
    except Exception as e:
        logger.exception(f"Error executing tool cancel_subscription: {e}")
        raise e
