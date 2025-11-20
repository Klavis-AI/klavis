import logging
import base64
import json
import os
from typing import Any, Dict, Tuple
from contextvars import ContextVar
import httpx

# Configure logging
logger = logging.getLogger(__name__)

GONG_API_ENDPOINT = "https://api.gong.io"

# Context variables to store the access key and secret for each request
# These are used to construct the Basic Auth header as per Gong API requirements
access_key_context: ContextVar[str] = ContextVar("access_key")
access_key_secret_context: ContextVar[str] = ContextVar("access_key_secret")

def extract_credentials(request_or_scope) -> Dict[str, str]:
    """Extract access key and secret credentials from x-auth-data header or environment variables.
    
    Returns:
        Dict with 'access_key' and 'access_key_secret' keys
    """
    access_key = os.getenv("GONG_ACCESS_KEY")
    access_key_secret = os.getenv("GONG_ACCESS_KEY_SECRET")
    
    auth_data = None
    # Handle different input types (request object for SSE, scope dict for StreamableHTTP)
    if hasattr(request_or_scope, 'headers'):
        # SSE request object
        auth_data_header = request_or_scope.headers.get(b'x-auth-data')
        if auth_data_header:
            auth_data = base64.b64decode(auth_data_header).decode('utf-8')
    elif isinstance(request_or_scope, dict) and 'headers' in request_or_scope:
        # StreamableHTTP scope object
        headers = dict(request_or_scope.get("headers", []))
        auth_data_header = headers.get(b'x-auth-data')
        if auth_data_header:
            auth_data = base64.b64decode(auth_data_header).decode('utf-8')
    
    # If no credentials from environment, try to parse from auth_data (from prod)
    if auth_data and (not access_key or not access_key_secret):
        try:
            # Parse the JSON auth data to extract credentials
            auth_json = json.loads(auth_data)
            access_key = auth_json.get('access_key', '') or access_key
            access_key_secret = auth_json.get('access_key_secret', '') or access_key_secret
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to parse auth data JSON: {e}")
    
    return {
        'access_key': access_key or "",
        'access_key_secret': access_key_secret or "",
    }

def get_credentials() -> Tuple[str, str]:
    """Get the access key and secret from context or environment.
    
    Returns:
        Tuple of (access_key, access_key_secret)
    """
    # First try to get from context variables
    try:
        access_key = access_key_context.get()
        access_key_secret = access_key_secret_context.get()
        if access_key and access_key_secret:
            return access_key, access_key_secret
    except LookupError:
        pass
    
    # Fall back to environment variables
    access_key = os.getenv("GONG_ACCESS_KEY", "")
    access_key_secret = os.getenv("GONG_ACCESS_KEY_SECRET", "")
    
    if not access_key or not access_key_secret:
        raise RuntimeError(
            "Gong credentials not found. Please provide them via x-auth-data header "
            "with 'access_key' and 'access_key_secret' fields, "
            "or set GONG_ACCESS_KEY and GONG_ACCESS_KEY_SECRET environment variables."
        )
    
    return access_key, access_key_secret

def build_headers(extra: Dict[str, str] | None = None) -> Dict[str, str]:
    """Helper to construct request headers with Basic Authorization and JSON content type.
    
    The Authorization header is constructed as per Gong API requirements:
    Base64(accessKey:accessKeySecret) prefixed with 'Basic '
    """
    access_key, access_key_secret = get_credentials()
    
    # Construct Basic Auth header: Base64(accessKey:accessKeySecret)
    credentials = f"{access_key}:{access_key_secret}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    
    headers: Dict[str, str] = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/json",
    }
    if extra:
        headers.update(extra)
    return headers

async def get(path: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Perform a GET request to the Gong API and return JSON."""
    url = f"{GONG_API_ENDPOINT}{path}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, headers=build_headers())
        resp.raise_for_status()
        return resp.json()

async def post(path: str, json_body: Dict[str, Any]) -> Dict[str, Any]:
    """Perform a POST request to the Gong API and return JSON."""
    url = f"{GONG_API_ENDPOINT}{path}"
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=json_body, headers=build_headers())
        resp.raise_for_status()
        return resp.json() 