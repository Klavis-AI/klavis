
from typing import Any, Dict, Optional, List
import logging

from .base import RazorpayClient
from .Constants import Version

logger = logging.getLogger(__name__)

version = Version.V1


async def create_payment_link(
    amount: int,
    description: str,
    currency: Optional[str] = None,
    accept_partial: Optional[bool] = None,
    first_min_partial_amount: Optional[int] = None,
    upi_link: Optional[bool] = None,
    customer: Optional[Dict[str, str]] = None,
    expire_by: Optional[int] = None,
    reference_id: Optional[str] = None,
    notify: Optional[Dict[str, bool]] = None,
    reminder_enable: Optional[bool] = None,
    notes: Optional[Dict[str, Any]] = None,
    callback_url: Optional[str] = None,
    callback_method: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates a Razorpay Payment Link.

    Args:
        amount (int): Amount in the smallest currency unit.
        description (str): A description for the payment link.
        currency (Optional[str]): 3-letter ISO currency code. Defaults to 'INR'.
        accept_partial (Optional[bool]): If partial payments are allowed.
        first_min_partial_amount (Optional[int]): The minimum first partial payment amount.
        upi_link (Optional[bool]): True to create a UPI Payment Link.
        customer (Optional[Dict[str, str]]): A dict with 'name', 'email', and 'contact'.
        expire_by (Optional[int]): Unix timestamp for when the link should expire.
        reference_id (Optional[str]): A unique reference ID.
        notify (Optional[Dict[str, bool]]): A dict with 'sms' and 'email' booleans for notifications.
        reminder_enable (Optional[bool]): To enable payment reminders.
        notes (Optional[Dict[str, Any]]): Key-value pairs for additional information.
        callback_url (Optional[str]): URL to redirect the customer to after payment.
        callback_method (Optional[str]): Must be 'get' if callback_url is provided.

    Returns:
        A dictionary containing the created payment link details on success, or an error dictionary.
    """
    # --- Input Validation ---
    if not isinstance(amount, int) or amount <= 0:
        raise ValueError("Field 'amount' is required and must be a positive integer.")
    if not isinstance(description, str):
        raise ValueError("Field 'description' is required and must be a string.")
    if callback_url is not None and callback_method is None:
        raise ValueError("Field 'callback_method' is required when 'callback_url' is provided.")

    # --- Payload Construction ---
    payload = {"amount": amount, "description": description}

    if currency is not None:
        if not isinstance(currency, str) or len(currency) != 3:
            raise ValueError("Field 'currency' must be a 3-letter string (e.g., 'INR').")
        payload["currency"] = currency.upper()

    if accept_partial is not None:
        if not isinstance(accept_partial, bool):
            raise ValueError("Field 'accept_partial' must be a boolean.")
        payload["accept_partial"] = accept_partial
        
    if first_min_partial_amount is not None:
        if not accept_partial:
            raise ValueError("'first_min_partial_amount' can only be used when 'accept_partial' is True.")
        if not isinstance(first_min_partial_amount, int):
            raise ValueError("Field 'first_min_partial_amount' must be an integer.")
        payload["first_min_partial_amount"] = first_min_partial_amount

    # Add other optional fields to payload if they are provided
    if upi_link is not None: payload["upi_link"] = upi_link
    if reference_id is not None: payload["reference_id"] = reference_id
    if customer is not None: payload["customer"] = customer
    if expire_by is not None: payload["expire_by"] = expire_by
    if notify is not None: payload["notify"] = notify
    if notes is not None: payload["notes"] = notes
    if callback_url is not None: payload["callback_url"] = callback_url
    if callback_method is not None: payload["callback_method"] = callback_method
    if reminder_enable is not None: payload["reminder_enable"] = reminder_enable

    # --- API Call ---
    try:
        result = await RazorpayClient.make_request(
            method="POST",
            endpoint="/payment_links",
            data=payload,
            version=version
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception(f"Razorpay API call failed while creating payment link: {e}")
        return {
            "success": False,
            "error": "An external API error occurred while creating payment link",
            "details": str(e),
        }


async def update_payment_link(
    payment_link_id: str,
    reference_id: Optional[str] = None,
    expire_by: Optional[int] = None,
    notes: Optional[Dict[str, Any]] = None,
    accept_partial: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Updates an existing Standard Payment Link.

    Args:
        payment_link_id (str): The ID of the payment link to update.
        reference_id (Optional[str]): The new reference ID.
        expire_by (Optional[int]): The new expiry timestamp.
        notes (Optional[Dict[str, Any]]): The new notes object.
        accept_partial (Optional[bool]): The new value for accepting partial payments.

    Returns:
        A dictionary containing the updated payment link details or an error dictionary.
    """
    if not payment_link_id or not isinstance(payment_link_id, str):
        raise ValueError('payment_link_id must be a non-empty string')

    payload = {}
    if reference_id is not None:
        if not isinstance(reference_id, str):
            raise ValueError("Field 'reference_id' must be a string.")
        payload["reference_id"] = reference_id

    if expire_by is not None:
        if not isinstance(expire_by, int):
            raise ValueError("Field 'expire_by' must be an integer (Unix timestamp).")
        payload["expire_by"] = expire_by

    if notes is not None:
        if not isinstance(notes, dict):
            raise ValueError("Field 'notes' must be a dictionary.")
        payload["notes"] = notes

    if accept_partial is not None:
        if not isinstance(accept_partial, bool):
            raise ValueError("Field 'accept_partial' must be a boolean.")
        payload["accept_partial"] = accept_partial
        
    if not payload:
        raise ValueError("At least one field to update must be provided.")

    try:
        result = await RazorpayClient.make_request(
            method="PATCH",
            endpoint=f"/payment_links/{payment_link_id}",
            data=payload,
            version=version
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception(f"Razorpay API call failed while updating payment link: {e}")
        return {
            "success": False,
            "error": "Razorpay API call failed while updating payment link",
            "details": str(e)
        }



async def fetch_all_payment_links(
    payment_link_id: Optional[str] = None,
    reference_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetches a list of Razorpay Payment Links with optional filters.

    Args:
        payment_id (Optional[str]): Filter links by the associated payment ID.
        reference_id (Optional[str]): Filter links by the unique reference ID.

    Returns:
        A dictionary containing the list of payment links on success,
        or an error dictionary on failure.
    """
    params = {}

    if payment_link_id is not None:
        if not isinstance(payment_link_id, str) or not payment_link_id:
            raise ValueError("Parameter 'payment_link_id' must be a non-empty string.")
        params["payment_id"] = payment_link_id

    if reference_id is not None:
        if not isinstance(reference_id, str) or not reference_id:
            raise ValueError("Parameter 'reference_id' must be a non-empty string.")
        params["reference_id"] = reference_id

    try:
        result = await RazorpayClient.make_request(
            method="GET",
            endpoint="/payment_links/",
            params=params,
            data=None,
            version=version
        )
        return {"success": True, "data": result}

    except Exception as e:
        logger.exception(f"Razorpay API call failed while fetching payment links: {e}")
        return {
            "success": False,
            "error": "An external API error occurred while fetching payment links",
            "details": str(e),
        }
    
async def fetch_payment_links_with_id(
    payment_link_id: str
) -> Dict[str, Any]:
    """
    Fetches a list of Razorpay Payment Links with id.

    Args:
        payment_id (str): Filter links by the associated payment ID.
    

    Returns:
        A dictionary containing the list of payment links on success,
        or an error dictionary on failure.
    """
    
    if not isinstance(payment_link_id, str) or not payment_link_id:
        raise ValueError("Parameter 'payment_id' must be a non-empty string.")
      
    try:
        result = await RazorpayClient.make_request(
            method="GET",
            endpoint=f"/payment_links/{payment_link_id}",
            params=None,
            data=None,
            version=version
        )
        return {"success": True, "data": result}

    except Exception as e:
        logger.exception(f"Razorpay API call failed while fetching payment link with id: {e}")
        return {
            "success": False,
            "error": "An external API error occurred while fetching payment link with id",
            "details": str(e),
        }

async def send_or_resend_payment_link_notifications(
    payment_link_id: str,
    medium: str
) -> Dict[str, Any]:
    """
    Sends or resends a notification for a specific Payment Link via SMS or email.

    Args:
        payment_link_id (str): The unique ID of the Payment Link .
        medium (str): The medium for the notification. Must be either 'sms' or 'email'.

    Returns:
        A dictionary with a success message, or an error dictionary on failure.
    """
    medium = medium.lower()
    if not payment_link_id or not isinstance(payment_link_id, str):
        raise ValueError("Parameter 'payment_link_id' must be a non-empty string.")

    if not medium or not isinstance(medium, str) or medium not in {'sms', 'email'}:
        raise ValueError("Parameter 'medium' must be either 'sms' or 'email'.")

    endpoint = f"/payment_links/{payment_link_id}/notify_by/{medium}"

    try:
        result = await RazorpayClient.make_request(
            method="POST",
            endpoint=endpoint,
            data=None, 
            params=None,
            version=version
        )
        return {"success": True, "data": result}

    except Exception as e:
        logger.exception(f"Razorpay API call failed while sending notification for link {payment_link_id}: {e}")
        return {
            "success": False,
            "error": f"An external API error occurred while sending notification for link {payment_link_id}",
            "details": str(e),
        }
    

async def cancel_payment_link(
        payment_link_id:str
)->Dict[str,Any]:
    
    """
    Use this function to cancel payment link by providing payment_link_id
    Args:
        payment_link_id:str
    Returns:
        Cancelled payment link info dictionary or failed dictionary

    """
    
    if(not payment_link_id or not isinstance(payment_link_id,str)):
        raise ValueError('Payment Link id must be provided as a string')
    
    try:
        result = await RazorpayClient.make_request(
            method="POST",
            endpoint=f"/payment_links/{payment_link_id}/cancel",
            params=None,
            data=None,
            version=version
        )

        return {"success":True, "data":result}

    except Exception as e:
        logger.exception(f"Razorpay API call failed while cancelling payment link: {e}")
        return {
        "success": False,
        "error": "Razorpay API call failed while cancelling payment link",
        "details": str(e)
        }
    
