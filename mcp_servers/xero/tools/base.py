import logging
import os
from contextvars import ContextVar
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import httpx

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

# Context variable to store the access token for each request
auth_token_context: ContextVar[str] = ContextVar('auth_token')

def get_auth_token() -> str:
    """Get the authentication token from context."""
    try:
        token = auth_token_context.get()
        if not token:
            # Fallback to environment variable if no token in context
            token = os.getenv("XERO_ACCESS_TOKEN")
            if not token:
                raise RuntimeError("No authentication token available")
        return token
    except LookupError:
        token = os.getenv("XERO_ACCESS_TOKEN")
        if not token:
            raise RuntimeError("Authentication token not found in request context or environment")
        return token

def get_tenant_id() -> str:
    """Get the Xero tenant ID from environment."""
    tenant_id = os.getenv("XERO_TENANT_ID")
    if not tenant_id:
        raise RuntimeError("XERO_TENANT_ID not found in environment")
    return tenant_id

async def make_xero_api_request(endpoint: str, method: str = "GET", data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Make a direct HTTP request to Xero API."""
    try:
        auth_token = get_auth_token()
        tenant_id = get_tenant_id()
        
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Xero-tenant-id": tenant_id,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        url = f"https://api.xero.com/api.xro/2.0/{endpoint}"
        
        async with httpx.AsyncClient() as client:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = await client.put(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
    except Exception as e:
        logger.error(f"Error making Xero API request to {endpoint}: {e}")
        raise