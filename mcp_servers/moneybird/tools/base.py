import logging
import os
from typing import Any, Dict, Optional
from contextvars import ContextVar
import httpx
from dotenv import load_dotenv

# Load env vars from .env
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

MONEYBIRD_API_ENDPOINT = "https://moneybird.com/api/v2"

# Context variable to store the API key for each request
auth_token_context: ContextVar[str] = ContextVar('auth_token')

def get_auth_token() -> str:
    """
    Get the Moneybird API token from context or fallback to env.
    """
    try:
        token = auth_token_context.get()
        if not token:
            # Fallback to environment variable
            token = os.getenv("MONEYBIRD_API_TOKEN")
            logger.debug(f"Using token from environment: {bool(token)}")
            if not token:
                raise RuntimeError("No Moneybird auth token found in context or environment")
        return token
    except LookupError:
        # Context variable not set at all
        token = os.getenv("MONEYBIRD_API_TOKEN")
        if not token:
            raise RuntimeError("No Moneybird auth token found in context or environment")
        return token

class MoneybirdClient:
    """Client for Moneybird API v2 using Bearer Authentication."""
    
    @staticmethod
    async def make_request(
        method: str, 
        administration_id: str,
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to Moneybird API."""
        api_key = get_auth_token()
        
        if not api_key:
            raise RuntimeError("No API key provided. Please set the x-auth-token header.")
        
        # Moneybird uses Bearer Authentication
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Moneybird API structure: /api/v2/:administration_id/:endpoint
        url = f"{MONEYBIRD_API_ENDPOINT}/{administration_id}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = await client.put(url, headers=headers, json=data)
            elif method.upper() == "PATCH":
                response = await client.patch(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            # Handle empty responses for DELETE operations
            if response.status_code == 204 or not response.content:
                return {"success": True}
            
            try:
                json_response = response.json()
                # Handle null/undefined responses
                if json_response is None:
                    return {"data": None, "message": "API returned null response"}
                return json_response
            except ValueError as e:
                # Handle cases where response content exists but isn't valid JSON
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response content: {response.content}")
                return {"error": "Invalid JSON response", "content": response.text}

async def make_request(
    method: str, 
    administration_id: str,
    endpoint: str, 
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Make an HTTP request to Moneybird API."""
    return await MoneybirdClient.make_request(method, administration_id, endpoint, data, params)