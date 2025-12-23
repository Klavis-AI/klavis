import logging
import json
from typing import Any, Dict, Optional, List
from .base import RazorpayClient
from .Constants import Version,VALID_EXPAND_VALUES_ORDERS

logger = logging.getLogger(__name__)

# Base URL for every order endpoint is V1 
version = Version.V1

async def create_order(
    amount: int,
    currency: str,
    receipt: Optional[str] = None,
    notes: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Creates a new Razorpay Order.

    Args:
        amount (int): Amount in the smallest currency unit (e.g., 50000 for ₹500.00).
        currency (str): 3-letter ISO currency code (e.g., 'INR').
        receipt (Optional[str]): A unique receipt ID for your reference (max 40 chars).
        notes (Optional[Dict[str, Any]]): Key-value pairs for additional information.

    Returns:
        A dictionary containing the created order details or an error dictionary.
    """
    # --- Input Validation ---
    if not isinstance(amount, int) or amount <= 0:
        raise ValueError("Field 'amount' must be a positive integer.")
    if not isinstance(currency, str) or len(currency) != 3:
        raise ValueError("Field 'currency' must be a 3-letter string (e.g., 'INR').")

    # --- Payload Construction ---
    payload = {
        "amount": amount,
        "currency": currency,
    }

    if receipt is not None:
        if not isinstance(receipt, str):
            raise ValueError("Field 'receipt' must be a string.")
        if len(receipt) > 40:
            raise ValueError("Field 'receipt' cannot exceed 40 characters.")
        payload["receipt"] = receipt

    if notes is not None:
        if not isinstance(notes, dict):
            raise ValueError("Field 'notes' must be a dictionary.")
        if len(notes) > 15:
            raise ValueError("Field 'notes' cannot have more than 15 key-value pairs.")
        payload["notes"] = notes
    
    # --- API Call ---
    try:
        result = await RazorpayClient.make_request(
            method="POST",
            endpoint="/orders",
            data=payload,
            version=version
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception(f"Razorpay API call failed while creating order: {e}")
        return {
            "success": False,
            "error": "Razorpay API call failed while creating order",
            "details": str(e)
        }


async def update_order(
    order_id: str,
    notes: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Updates the notes for an existing order.

    Args:
        order_id (str): The unique ID of the order to update.
        notes (Dict[str, Any]): The key-value pairs to set as notes.

    Returns:
        A dictionary containing the updated order details or an error dictionary.
    """
    # --- Input Validation ---
    if not order_id or not isinstance(order_id, str):
        raise ValueError('Order ID must be a non-empty string.')
    if not isinstance(notes, dict):
        raise ValueError('Notes field must be provided as a dictionary.')

    payload = {"notes": notes}
    
    # --- API Call ---
    try:
        result = await RazorpayClient.make_request(
            method="PATCH",
            endpoint=f"/orders/{order_id}",
            data=payload,
            version=version
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception(f"Razorpay API call failed while updating order: {e}")
        return {
            "success": False,
            "error": "Razorpay API call failed while updating order",
            "details": str(e)
        }


async def fetch_all_orders(
    from_ts: Optional[int] = None,
    to_ts: Optional[int] = None,
    count: Optional[int] = None,
    skip: Optional[int] = None,
    authorized: Optional[bool] = None,
    receipt: Optional[str] = None,
    expand: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Fetches a list of Razorpay Orders based on specified criteria.

    Args:
        from_ts : Unix timestamp 
        to_ts : Unix timestamp
        count : The number of orders to fetch (default 10, max 100).
        skip : The number of orders to skip (for pagination).
        authorized : Set to True to fetch authorized orders, False for unauthorized.
        receipt : The specific receipt ID to search for.
        expand : A list of sub-entities to expand in the response.
                  Valid values are: 'payments', 'payments.card', 'transfers', 'virtual_account'.

    Returns:
        A dictionary containing the list of orders on success,
        or an error dictionary on failure.
    """
    params = {}

    # This block validates each parameter and adds it to the `params` dict if it's valid.
    if from_ts is not None:
        if not isinstance(from_ts, int) or from_ts < 0:
            raise ValueError("Parameter 'from_ts' must be a positive integer Unix timestamp.")
        params["from"] = from_ts

    if to_ts is not None:
        if not isinstance(to_ts, int) or to_ts < 0:
            raise ValueError("Parameter 'to_ts' must be a positive integer Unix timestamp.")
        params["to"] = to_ts

    if count is not None:
        if not isinstance(count, int) or not (1 <= count <= 100):
            raise ValueError("Parameter 'count' must be an integer between 1 and 100.")
        params["count"] = count

    if skip is not None:
        if not isinstance(skip, int) or skip < 0:
            raise ValueError("Parameter 'skip' must be a non-negative integer.")
        params["skip"] = skip

    if authorized is not None:
        if not isinstance(authorized, bool):
            raise ValueError("Parameter 'authorized' must be a boolean (True or False).")
        params["authorized"] = 1 if authorized else 0

    if receipt is not None:
        if not isinstance(receipt, str):
            raise ValueError("Parameter 'receipt' must be a string.")
        params["receipt"] = receipt
        
    if expand is not None:
        if not isinstance(expand, list) or not all(isinstance(item, str) for item in expand):
            raise ValueError("Parameter 'expand' must be a list of strings.")
        
        for item in expand:
            if item not in VALID_EXPAND_VALUES_ORDERS:
                raise ValueError(f"Invalid expand value '{item}'. Allowed values are: {VALID_EXPAND_VALUES_ORDERS}")
            
        params["expand[]"] = expand

    try:
        result = await RazorpayClient.make_request(
            method="GET",
            endpoint="/orders",
            params=params,  
            data=None,
            version=version
        )
        return {"success": True, "data": result}

    except Exception as e:
        logger.exception(f"Razorpay API call failed while fetching orders: {e}")
        return {
            "success": False,
            "error": "An external API error occurred while fetching orders",
            "details": str(e),
        }


async def fetch_order_by_id(
      order_id:str
)->Dict[str,Any]:
   """
    Use this endpoint to fetch order by id.
   Args:
      order_id:string
    Returns:
      fetched order dictionary or failed dictionary.

   """
   
   if not order_id or not isinstance(order_id, str):
      raise ValueError('Order id must be provided as a string')
   
   try:
      result = await RazorpayClient.make_request(
         method="GET",
         endpoint=f"/orders/{order_id}",
         params=None,
         data=None,
         version=version
      )

      return {"success":True, "data":result}

   except Exception as e:
      logger.exception(f"Razorpay API call failed while fetching order by order_id: {e}")
      return {
        "success": False,
        "error": "Razorpay API call failed while fetching order by order_id",
        "details": str(e)
      }

async def fetch_payments_by_order_id(
      order_id:str
)->Dict[str,Any]:
   """
   Use this endpoint to fetch all the payments made for an order. The response contains all the authorised or failed payments for that order.
   Args:
      order_id:string
    Returns:
      all the authorised or failed payments for that order.
   """
   
   if(len(order_id) == 0 or not order_id):
      raise ValueError('Order id must not be empty')
   
   try:
      result = await RazorpayClient.make_request(
         method="GET",
         endpoint=f"/orders/{order_id}/payments",
         params=None,
         data=None,
         version=version
      )

      return {"success":True, "data":result}

   except Exception as e:
      logger.exception(f"Razorpay API call failed while fetching payments by order_id: {e}")
      return {
        "success": False,
        "error": "Razorpay API call failed while fetching payments by order_id",
        "details": str(e)
      }
    