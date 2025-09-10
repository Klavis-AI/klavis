
from typing import Any, Dict, Optional, List
import logging

from .base import RazorpayClient
from .Constants import Version

logger = logging.getLogger(__name__)

version = Version.V1

async def create_QR_code(
    type: str,
    usage: str,
    name: Optional[str] = None,
    fixed_amount: Optional[bool] = None,
    payment_amount: Optional[int] = None,
    description: Optional[str] = None,
    customer_id: Optional[str] = None,
    close_by: Optional[int] = None,
    notes: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Creates a Razorpay QR Code.

    Args:
        type (str): The type of QR Code. Must be 'upi_qr'.
        usage (str): Usage type. Must be 'single_use' or 'multiple_use'.
        name (Optional[str]): A name or label for the QR Code.
        fixed_amount (Optional[bool]): If the QR code is for a fixed amount.
        payment_amount (Optional[int]): The fixed amount in currency subunits.
        description (Optional[str]): A description for the QR Code.
        customer_id (Optional[str]): The ID of the customer it is assigned to.
        close_by (Optional[int]): Unix timestamp for when a single_use QR code expires.
        notes (Optional[Dict[str, Any]]): Key-value pairs for additional information.

    Returns:
        A dictionary containing the created QR Code details or an error dictionary.
    """
    if type != 'upi_qr':
        raise ValueError("Field 'type' is required and must be 'upi_qr'.")
    if usage not in {'single_use', 'multiple_use'}:
        raise ValueError("Field 'usage' is required and must be either 'single_use' or 'multiple_use'.")
    if usage == 'single_use' and fixed_amount is not True:
        raise ValueError("For 'single_use' QR Codes, 'fixed_amount' must be set to True.")
    if close_by is not None and usage != 'single_use':
        raise ValueError("Parameter 'close_by' is only available for 'single_use' QR Codes.")

    payload = {"type": type, "usage": usage}

    if name is not None:
        payload["name"] = name
    if fixed_amount is not None:
        payload["fixed_amount"] = fixed_amount
    if payment_amount is not None:
        payload["payment_amount"] = payment_amount
    if description is not None:
        payload["description"] = description
    if customer_id is not None:
        payload["customer_id"] = customer_id
    if close_by is not None:
        payload["close_by"] = close_by
    if notes is not None:
        if not isinstance(notes, dict) or len(notes) > 15:
            raise ValueError("Field 'notes' must be a dictionary with no more than 15 key-value pairs.")
        payload["notes"] = notes

    try:
        result = await RazorpayClient.make_request(
            method="POST",
            endpoint="/payments/qr_codes",
            data=payload,
            version=version
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception(f"Razorpay API call failed while creating QR code: {e}")
        return {
            "success": False,
            "error": "An external API error occurred while creating QR code",
            "details": str(e),
        }


    
async def close_QR_code(
    qr_id:str      
)->Dict[str,Any]:
    
    """
    Use this function to close QR code by providing QR id
    Args:
        qr_id:str
    Returns:
        Closed QR code info dictionary or failed dictionary
    
    """
    
    if(not qr_id or not isinstance(qr_id,str)):
        raise ValueError('QR Id must be a string')
    
    try:
        result = await RazorpayClient.make_request(
            method="POST",
            endpoint=f"/payments/qr_codes/{qr_id}/close",
            params=None,
            data=None,
            version=version
        )

        return {"success":True, "data":result}

    except Exception as e:
        logger.exception(f"Razorpay API call failed while closing QR code: {e}")
        return {
        "success": False,
        "error": "Razorpay API call failed while closing QR code",
        "details": str(e)
        }
    
async def fetch_all_QR_codes(
    from_ts: Optional[int] = None,
    to_ts: Optional[int] = None,
    count: Optional[int] = None,
    skip: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Use this function to retrieve the details of multiple QR Codes.
    Args:
        from_ts : Unix timestamp 
        to_ts : Unix timestamp
        count : The number of QR codes to fetch (default 10, max 100).
        skip : The number of QR codes to skip (for pagination).

    Returns:
        A dictionary containing the list of QR codes on success,
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

    try:
        result = await RazorpayClient.make_request(
            method="GET",
            endpoint="/payments/qr_codes",
            params=params,  
            data=None,
            version=version
        )
        return {"success": True, "data": result}

    except Exception as e:
        logger.exception(f"Razorpay API call failed while fetching QR codes: {e}")
        return {
            "success": False,
            "error": "An external API error occurred while fetching QR codes",
            "details": str(e),
        }
    

async def fetch_QR_code_by_id(
    qr_id:str      
)->Dict[str,Any]:
    
    """
    Use this endpoint to fetch the details of a QR Code.
    Args:
        QR id : str
    Returns:
        QR code fetched by id or error dictionary on failure
    """
    
    if(not qr_id or not isinstance(qr_id,str)):
        raise ValueError('QR Id must be a string')
    
    try:
        result = await RazorpayClient.make_request(
            method="GET",
            endpoint=f"/payments/qr_codes/{qr_id}",
            params=None,
            data=None,
            version=version
        )

        return {"success":True, "data":result}

    except Exception as e:
        logger.exception(f"Razorpay API call failed while fetching QR code by id: {e}")
        return {
        "success": False,
        "error": "Razorpay API call failed while fetching QR code by id",
        "details": str(e)
        }
    

async def update_QR_code(
    qr_id: str,
    notes: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Updates the notes for an existing QR code.

    Args:
        qr_id (str): The unique ID of the QR code to update.
        notes (Dict[str, Any]): The key-value pairs to set as notes.

    Returns:
        A dictionary containing the updated QR code details or an error dictionary.
    """
    if not qr_id or not isinstance(qr_id, str):
        raise ValueError('QR ID must be a non-empty string.')
    
    if not isinstance(notes, dict):
        raise ValueError('Notes field must be provided in dictionary format.')

    payload = {"notes": notes}
    
    try:
        result = await RazorpayClient.make_request(
            method="PATCH",
            endpoint=f"/payments/qr_codes/{qr_id}",
            data=payload,
            version=version
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception(f"Razorpay API call failed while updating QR code: {e}")
        return {
            "success": False,
            "error": "Razorpay API call failed while updating QR code",
            "details": str(e)
        }

