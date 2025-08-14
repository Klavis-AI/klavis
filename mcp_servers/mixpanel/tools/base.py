import logging
import json
import base64
from typing import Any, Dict, Optional
from contextvars import ContextVar
import httpx

logger = logging.getLogger(__name__)

MIXPANEL_INGESTION_ENDPOINT = "https://api.mixpanel.com"
MIXPANEL_EXPORT_ENDPOINT = "https://data.mixpanel.com/api"

project_token_context: ContextVar[str] = ContextVar('project_token')
api_secret_context: ContextVar[str] = ContextVar('api_secret')

def get_project_token() -> str:
    """Get the project token from context."""
    try:
        return project_token_context.get()
    except LookupError:
        raise RuntimeError("Project token not found in request context")

def get_api_secret() -> str:
    """Get the API secret from context."""
    try:
        return api_secret_context.get()
    except LookupError:
        raise RuntimeError("API secret not found in request context")

# Add service account context variables
service_account_username_context: ContextVar[str] = ContextVar('service_account_username')
service_account_secret_context: ContextVar[str] = ContextVar('service_account_secret')

def get_service_account_username() -> str:
    """Get the service account username from context."""
    try:
        return service_account_username_context.get()
    except LookupError:
        raise RuntimeError("Service account username not found in request context")

def get_service_account_secret() -> str:
    """Get the service account secret from context."""
    try:
        return service_account_secret_context.get()
    except LookupError:
        raise RuntimeError("Service account secret not found in request context")

class MixpanelIngestionClient:
    """Client for Mixpanel Event Ingestion API."""
    
    @staticmethod
    async def make_request(
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to Mixpanel Ingestion API."""
        project_token = get_project_token()
        
        if not project_token:
            raise RuntimeError("No project token provided. Please set the project token.")
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/plain"
        }
        
        url = f"{MIXPANEL_INGESTION_ENDPOINT}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            if method.upper() == "POST":
                response = await client.post(url, headers=headers, json=data, params=params)
            elif method.upper() == "GET":
                response = await client.get(url, headers=headers, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method for ingestion: {method}")
            
            response.raise_for_status()
            
            # Mixpanel ingestion API typically returns "1" for success or error details
            if response.text == "1":
                return {"success": True, "message": "Event tracked successfully"}
            elif response.text == "0":
                return {"success": False, "error": "Event tracking failed"}
            else:
                # Try to parse as JSON for error details
                try:
                    return response.json()
                except ValueError:
                    return {"success": False, "error": response.text}

class MixpanelQueryClient:
    """Client for Mixpanel Query/Export API."""
    
    @staticmethod
    async def make_request(
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to Mixpanel Query API."""
        # Try API secret first (more reliable), then service account
        auth = None
        
        try:
            api_secret = get_api_secret()
            if api_secret:
                auth = httpx.BasicAuth(api_secret, "")
                logger.info("Using API secret authentication for query")
        except RuntimeError:
            # Fall back to service account
            try:
                username = get_service_account_username()
                secret = get_service_account_secret()
                if username and secret:
                    auth = httpx.BasicAuth(username, secret)
                    logger.info("Using service account authentication for query")
            except RuntimeError:
                pass
        
        if not auth:
            raise RuntimeError("No authentication provided. Please set either service account credentials or API secret.")
        
        headers = {
            "Content-Type": "application/json"
        }
        
        url = f"{MIXPANEL_EXPORT_ENDPOINT}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            if method.upper() == "GET":
                response = await client.get(url, auth=auth, headers=headers, params=params)
            elif method.upper() == "POST":
                response = await client.post(url, auth=auth, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method for query: {method}")
            
            response.raise_for_status()
            
            # Handle different response types
            content_type = response.headers.get("content-type", "")
            
            if "application/json" in content_type:
                return response.json()
            elif response.text:
                # Some endpoints return newline-delimited JSON
                if endpoint.startswith("/2.0/export"):
                    lines = response.text.strip().split('\n')
                    events = []
                    for line in lines:
                        if line:
                            try:
                                events.append(json.loads(line))
                            except ValueError:
                                continue
                    return {"events": events}
                else:
                    try:
                        return response.json()
                    except ValueError:
                        return {"data": response.text}
            else:
                return {"success": True}

async def make_query_request(
    method: str, 
    endpoint: str, 
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Make an HTTP request to Mixpanel Query API."""
    return await MixpanelQueryClient.make_request(method, endpoint, data, params)