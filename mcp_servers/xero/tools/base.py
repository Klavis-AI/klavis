import os
import logging
from typing import Any, Dict, Optional
from contextvars import ContextVar
import httpx

# Configure logging
logger = logging.getLogger(__name__)

XERO_API_ENDPOINT = "https://api.xero.com/api.xro/2.0"

# Context variable to store the API key for each request
auth_token_context: ContextVar[str] = ContextVar('auth_token')

def get_auth_token() -> str:
    """Get the authentication token from context."""
    try:
        return auth_token_context.get()
    except LookupError:
        raise RuntimeError("Authentication token not found in request context")

def get_xero_tenant_id() -> str:
    """Get the Xero tenant ID from environment."""
    tenant_id = os.getenv("XERO_TENANT_ID")
    if not tenant_id:
        raise RuntimeError("XERO_TENANT_ID not found in environment")
    return tenant_id

class XeroClient:
    """Client for Xero API using Bearer Authentication."""
    
    @staticmethod
    async def make_request(
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to Xero API."""
        api_key = get_auth_token()
        
        if not api_key:
            raise RuntimeError("No API key provided. Please set the x-auth-token header.")
        
        tenant_id = get_xero_tenant_id()
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Xero-tenant-id": tenant_id,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Ensure endpoint starts with proper format
        if not endpoint.startswith('/'):
            endpoint = f"/{endpoint}"
        
        url = f"{XERO_API_ENDPOINT}{endpoint}"
        
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

async def make_xero_api_request(
    endpoint: str, 
    method: str = "GET", 
    data: Optional[Dict[str, Any]] = None,
    expect_empty_response: bool = False
) -> Dict[str, Any]:
    """Make an HTTP request to Xero API."""
    # Note: expect_empty_response parameter is maintained for compatibility but not used
    # as the new implementation handles empty responses automatically
    return await XeroClient.make_request(method, endpoint, data)
