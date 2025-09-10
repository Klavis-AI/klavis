import logging
import json
import base64
import os
from typing import Any, Dict, Optional, Tuple
from enum import Enum
from contextvars import ContextVar
import httpx
from .Constants import Version

logger = logging.getLogger(__name__)


RAZORPAY_BASE_ENDPOINT_V1 = "https://api.razorpay.com/v1"
RAZORPAY_BASE_ENDPOINT_V2 = "https://api.razorpay.com/v2"

# Context Variables 
key_id_context = ContextVar("razorpay_key_id")
key_secret_context = ContextVar("razorpay_key_secret")



def get_razorpay_api_credentials() -> Tuple[str, str]:
    """Get razorpay api credentials from context or environment.
    
    Returns:
        Tuple of (razorpay_api_id, razorpay_account_secret)
    """
    # First try to get from context variables
    try:
        id = key_id_context.get()
        secret = key_secret_context.get()
        if id and secret:
            return id, secret
    except LookupError:
        pass
    
    # Fall back to environment variables
    id = os.getenv("RAZORPAY_API_ID", "")
    secret = os.getenv("RAZORPAY_API_SECRET", "")
    

    
    if not id or not secret:
        raise RuntimeError(
            f"{id} {secret}"
            "API credentials not found. Please provide them via x-auth-data header "
            "with 'razorpay_key_id' and 'razorpay_key_secret' fields, "
            "or set RAZORPAY_API_ID and "
            "RAZORPAY_API_SECRET environment variables."
        )
    
    return id, secret


class RazorpayClient:
    
    @staticmethod
    async def make_request(
        method: str,
        endpoint: str,
        version: Version,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        file_data:Optional[Dict[str,Any]] = None
    ) -> Dict[str, Any]:
        
        """Make an HTTP request to Razorpay API using Basic Auth in httpx.
        
        Args:
            method: HTTP method (e.g. GET, POST)
            endpoint: API endpoint (e.g. /payments, /orders)
            version: API Base URL version (Enum: Version.V1 / Version.V2)
            params: Optional query parameters.
            data: Optional request body data for POST, PATCH, PUT.
        """
        id, secret = get_razorpay_api_credentials()

        url = (RAZORPAY_BASE_ENDPOINT_V1 if version == Version.V1 else RAZORPAY_BASE_ENDPOINT_V2) + endpoint

        auth = httpx.BasicAuth(username=id, password=secret)

        async with httpx.AsyncClient(auth=auth) as client:
            request_method = method.upper()
            # Will be required when upload_document used
            if file_data:
                if request_method == "POST":
                    response = await client.post(url=url, files=file_data)
                else:
                    raise ValueError(f"File uploads are only supported for POST, not {request_method}")
            # For regular JSON requests
            else:
                print(url)
                headers = {"Content-Type": "application/json"}
                if request_method == "GET":
                    response = await client.get(url=url, params=params,headers=headers)
                elif request_method == "POST":
                    response = await client.post(url=url, params=params, json=data,files=file_data,headers=headers)
                elif request_method == "PUT":
                    response = await client.put(url=url, params=params, json=data,headers=headers)
                elif request_method == "PATCH":
                    response = await client.patch(url=url, params=params, json=data,headers=headers)
                elif request_method == "DELETE":
                    response = await client.delete(url=url, params=params,headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method for Razorpay API: {method}")

        response.raise_for_status()

        if not response.text:
            return {"success": True, "message": "Request successful with no content."}

        try:
            return response.json()
        except ValueError:
            return {"success": True, "message": response.text}