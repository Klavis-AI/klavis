import logging
from typing import Any, Dict, Optional, List

from .base import RazorpayClient
from .Constants import Version

logger = logging.getLogger(__name__)

version = Version.V1

async def fetch_payment_downtime_details()->Dict[str,Any]:

    """
    Use this endpoint to retrieve details of all payment downtimes.
    Args:
        Only Auth required
    Returns:
        Downtime details in form of dictionary or an error dictionary on failure
    """

    try:
        result = await RazorpayClient.make_request(
            method="GET",
            endpoint="/payments/downtimes",
            params=None,
            data=None,
            version=version
        )

        return {"success":True,"data":result}
    
    except Exception as e:
        logger.exception(f"Razorpay API call failed while fetching payment downtime details: {e}")
        return {
            "success": False,
            "error": "Razorpay API call failed while fetching payment downtime details",
            "details": str(e)
        }


async def fetch_payment_downtime_details_with_id(
        payment_id:str
)->Dict[str,Any]:
    """
    Use this endpoint to fetch downtime status if you have not received any webhook notifications due to technical issues. 
    Usually, downtime webhook payloads are delivered within few seconds of the event. 
    However, in some cases, this can be delayed by few minutes due to various reasons.
    
    Args:
        payment_id:str
    
    Returns:
        Downtime information about specified payment_id
    """

    if not payment_id or not isinstance(payment_id, str):
        raise ValueError("payment_id must be provided as a non-empty string.")
    try:
        result = await RazorpayClient.make_request(
            method="GET",
            endpoint=f"/payments/downtimes/{payment_id}",
            params=None,
            data=None,
            version=version
        )

        return {"success":True,"data":result}
    
    except Exception as e:
        logger.exception(f"Razorpay API call failed while fetching payment downtime details with id: {e}")
        return {
            "success": False,
            "error": "Razorpay API call failed while fetching payment downtime details with id",
            "details": str(e)
        }



    