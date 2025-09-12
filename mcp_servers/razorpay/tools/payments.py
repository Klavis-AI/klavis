import logging
import json
from typing import Any, Dict, Optional, List


from .base import RazorpayClient
from .Constants import Version,VALID_EXPAND_VALUES_PAYMENTS

logger = logging.getLogger(__name__)

# All payment APIs take V1 as base URL endpoint
version = Version.V1

async def capture_payment(
    payment_id: str,
    amount: int,
    currency: str
) -> Dict[str, Any]:
    """
    Captures a previously authorized payment.

    Args:
        payment_id (str): The unique ID of the payment to capture.
        amount (int): The amount to capture, in the smallest currency unit.
        currency (str): 3-letter ISO currency code.

    Returns:
        A dictionary containing the captured payment details or an error dictionary.
    """
    # --- Input Validation ---
    if not payment_id or not isinstance(payment_id, str):
        raise ValueError('Payment ID must be a non-empty string.')
    if not isinstance(amount, int) or amount <= 0:
        raise ValueError('Amount must be a positive integer.')
    if not isinstance(currency, str) or len(currency) != 3:
        raise ValueError('Currency must be a 3-letter string.')

    payload = {
        "amount": amount,
        "currency": currency
    }

    # --- API Call ---
    try:
        result = await RazorpayClient.make_request(
            method="POST",
            endpoint=f"/payments/{payment_id}/capture",
            data=payload,
            version=version
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception(f"Razorpay API call failed while capturing payment: {e}")
        return {
            "success": False,
            "error": "Razorpay API call failed while capturing payment",
            "details": str(e)
        }


async def update_payment(
    payment_id: str,
    notes: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Updates the notes for an existing payment.

    Args:
        payment_id (str): The unique ID of the payment to update.
        notes (Dict[str, Any]): The key-value pairs to set as notes.

    Returns:
        A dictionary containing the updated payment details or an error dictionary.
    """
    # --- Input Validation ---
    if not payment_id or not isinstance(payment_id, str):
        raise ValueError('Payment ID must be a non-empty string.')
    if not isinstance(notes, dict):
        raise ValueError('Notes field must be provided as a dictionary.')

    payload = {"notes": notes}

    # --- API Call ---
    try:
        result = await RazorpayClient.make_request(
            method="PATCH",
            endpoint=f"/payments/{payment_id}",
            data=payload,
            version=version
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception(f"Razorpay API call failed while updating payment: {e}")
        return {
            "success": False,
            "error": "Razorpay API call failed while updating payment",
            "details": str(e)
        }


async def fetch_all_payments(
    from_ts: Optional[int] = None,
    to_ts: Optional[int] = None,
    count: Optional[int] = None,
    skip: Optional[int] = None,
    expand: Optional[str]= None
) -> Dict[str, Any]:
    """
    Fetches a list of Razorpay payments based on specified criteria.

    Args:
        from_ts : Unix timestamp 
        to_ts : Unix timestamp
        count : The number of payments to fetch (default 10, max 100).
        skip : The number of payments to skip (for pagination).

    Returns:
        A dictionary containing the list of payments on success,
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

    if expand is not None:
        if not isinstance(expand, str):
            raise ValueError("Parameter 'expand' must be a  string.")
        
        if expand not in VALID_EXPAND_VALUES_PAYMENTS:
            raise ValueError(f"Invalid expand value '{expand}'. Allowed values are: {VALID_EXPAND_VALUES_PAYMENTS}")
            
        params["expand[]"] = expand


    try:
        result = await RazorpayClient.make_request(
            method="GET",
            endpoint="/payments",
            params=params,  
            data=None,
            version=version
        )
        return {"success": True, "data": result}

    except Exception as e:
        logger.exception(f"Razorpay API call failed while fetching payments: {e}")
        return {
            "success": False,
            "error": "An external API error occurred while fetching payments",
            "details": str(e),
        }

async def fetch_payment_by_id(
      payment_id:str,
      expand: Optional[str] = None
)->Dict[str,Any]:
   """
   Use this endpoint to retrieve the details of a specific payment using its id.
   Args:
    payment_id : str
   Returns:
    Payment dictionary or an error dictionary on failure.
   """
   
   if(len(payment_id) == 0 or not isinstance(payment_id,str)):
      raise ValueError('Payment id must be provided as a string')
   
   params={}
   if expand is not None:
        if not isinstance(expand, str):
            raise ValueError("Parameter 'expand' must be a  string.")
        
        if expand not in VALID_EXPAND_VALUES_PAYMENTS:
            raise ValueError(f"Invalid expand value '{expand}'. Allowed values are: {VALID_EXPAND_VALUES_PAYMENTS}")
            
        params["expand[]"] = expand
   
   try:
      result =await RazorpayClient.make_request(
         method="GET",
         endpoint=f"/payments/{payment_id}",
         params=params,
         data=None,
         version=version
      )

      return {"success":True, "data":result}

   except Exception as e:
      logger.exception(f"Razorpay API call failed while fetching payment by payment_id: {e}")
      return {
        "success": False,
        "error": "Razorpay API call failed while fetching payment by payment_id",
        "details": str(e)
      }
   
async def fetch_card_details_of_payment(
      payment_id:str
)->Dict[str,Any]:
   """
    Use this endpoint to retrieve the details of the card used to make a payment.  
   Args:
    payment_id : str
   Returns:
    Card object containing card details  or an error dictionary on failure.
   """
   
   if(len(payment_id) == 0 or not isinstance(payment_id,str)):
      raise ValueError('Payment id must be provided as a string')
   
   try:
      result =await RazorpayClient.make_request(
         method="GET",
         endpoint=f"/payments/{payment_id}/card",
         params=None,
         data=None,
         version=version
      )

      return {"success":True, "data":result}

   except Exception as e:
      logger.exception(f"Razorpay API call failed while fetching card details by payment_id: {e}")
      return {
        "success": False,
        "error": "Razorpay API call failed while fetching card details by payment_id",
        "details": str(e)
      }
   


