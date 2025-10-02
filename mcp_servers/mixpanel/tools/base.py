import logging
import json
import base64
import os
from typing import Any, Dict, Optional, Tuple
from contextvars import ContextVar
import httpx

logger = logging.getLogger(__name__)

# Mixpanel API Endpoints (as per https://developer.mixpanel.com/reference/overview)
MIXPANEL_INGESTION_ENDPOINT = "https://api.mixpanel.com"  # Ingestion API
MIXPANEL_EXPORT_ENDPOINT = "https://data.mixpanel.com/api/2.0/export"  # Raw Data Export API
MIXPANEL_QUERY_ENDPOINT = "https://mixpanel.com/api"  # Query API
MIXPANEL_APP_ENDPOINT = "https://mixpanel.com/api/app"  # App Management APIs (projects, GDPR, etc.)

# Context variables to store the credentials for each request
username_context: ContextVar[str] = ContextVar('serviceaccount_username')
secret_context: ContextVar[str] = ContextVar('serviceaccount_secret')

def get_service_account_credentials() -> Tuple[str, str]:
    """Get the service account credentials from context or environment.
    
    Returns:
        Tuple of (service_account_username, service_account_secret)
    """
    # First try to get from context variables
    try:
        username = username_context.get()
        secret = secret_context.get()
        if username and secret:
            return username, secret
    except LookupError:
        pass
    
    # Fall back to environment variables
    username = os.getenv("MIXPANEL_SERVICE_ACCOUNT_USERNAME", "")
    secret = os.getenv("MIXPANEL_SERVICE_ACCOUNT_SECRET", "")
    
    if not username or not secret:
        raise RuntimeError(
            "Service account credentials not found. Please provide them via x-auth-data header "
            "with 'serviceaccount_username' and 'serviceaccount_secret' fields, "
            "or set MIXPANEL_SERVICE_ACCOUNT_USERNAME and "
            "MIXPANEL_SERVICE_ACCOUNT_SECRET environment variables."
        )
    
    return username, secret

class MixpanelIngestionClient:
    """Client for Mixpanel Ingestion API using Service Account authentication.
    
    Ingestion API (api.mixpanel.com): For sending events, user profiles, and group data to Mixpanel.
    Supports /import for batch events and /engage for user profile updates.
    """
    
    @staticmethod
    async def make_request(
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to Mixpanel Ingestion API using Service Account auth.
        
        The ingestion API uses Service Account authentication for /import endpoint.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            project_id: Project ID for the import operation (required)
        """
        if not project_id:
            raise ValueError("project_id is required for ingestion operations")
            
        # Get service account credentials
        username, secret = get_service_account_credentials()
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/plain"
        }
        
        url = f"{MIXPANEL_INGESTION_ENDPOINT}{endpoint}"
        
        # Add project_id to params for /import endpoint
        if params is None:
            params = {}
        params["project_id"] = project_id
        
        # Use Basic Auth with service account credentials
        auth = httpx.BasicAuth(username, secret)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method.upper() == "POST":
                response = await client.post(url, auth=auth, headers=headers, json=data, params=params)
            elif method.upper() == "GET":
                response = await client.get(url, auth=auth, headers=headers, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method for ingestion: {method}")
        
        response.raise_for_status()
        
        # Handle response based on content type
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()
        elif response.text == "1":
            return {"success": True, "message": "Events imported successfully"}
        elif response.text == "0":
            return {"success": False, "error": "Event import failed"}
        else:
            # Try to parse as JSON for error details
            try:
                return response.json()
            except ValueError:
                return {"success": True, "message": response.text or "Import successful"}

class MixpanelExportClient:
    """Client for Mixpanel Raw Data Export API using Service Account authentication.
    
    Raw Data Export API (data.mixpanel.com/api/2.0/export): For exporting raw event data.
    """
    
    @staticmethod
    async def make_request(
        method: str, 
        endpoint: str = "", 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to Mixpanel Export API using Service Account authentication.
        
        Args:
            method: HTTP method
            endpoint: API endpoint (usually empty as the full path is in MIXPANEL_EXPORT_ENDPOINT)
            data: Request body data
            params: Query parameters
        """
        # Get service account credentials
        username, secret = get_service_account_credentials()
        
        # Use Basic Auth with service account credentials
        auth = httpx.BasicAuth(username, secret)
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # MIXPANEL_EXPORT_ENDPOINT already includes the full path /api/2.0/export
        url = MIXPANEL_EXPORT_ENDPOINT
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method.upper() == "GET":
                response = await client.get(url, auth=auth, headers=headers, params=params)
            elif method.upper() == "POST":
                response = await client.post(url, auth=auth, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method for export: {method}")
            
            response.raise_for_status()
            
            # Handle different response types
            content_type = response.headers.get("content-type", "")
            
            if "application/json" in content_type:
                return response.json()
            elif response.text:
                # The export endpoint returns newline-delimited JSON
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
                return {"success": True}

class MixpanelQueryClient:
    """Client for Mixpanel Query API using Service Account authentication.
    
    Query API (mixpanel.com/api): For calculated data like Insights, Funnels, Retention.
    """
    
    @staticmethod
    async def make_request(
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to Mixpanel Query API using Service Account authentication.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
        """
        # Get service account credentials
        username, secret = get_service_account_credentials()
        
        # Use Basic Auth with service account credentials
        auth = httpx.BasicAuth(username, secret)
        
        headers = {
            "Content-Type": "application/json"
        }
        
        url = f"{MIXPANEL_QUERY_ENDPOINT}{endpoint}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method.upper() == "GET":
                response = await client.get(url, auth=auth, headers=headers, params=params)
            elif method.upper() == "POST":
                response = await client.post(url, auth=auth, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method for query: {method}")
            
            response.raise_for_status()
            
            # Handle response
            content_type = response.headers.get("content-type", "")
            
            if "application/json" in content_type:
                return response.json()
            elif response.text:
                try:
                    return response.json()
                except ValueError:
                    return {"data": response.text}
            else:
                return {"success": True}

class MixpanelAppAPIClient:
    """Client for Mixpanel App Management API using Service Account authentication.
    
    App Management APIs (mixpanel.com/api/app): For project management, GDPR, schemas, etc.
    """
    
    @staticmethod
    async def make_request(
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to Mixpanel App Management API using Service Account authentication.
        
        Args:
            method: HTTP method
            endpoint: API endpoint (e.g., "/me", "/projects/{id}")
            data: Request body data
            params: Query parameters
        """
        # Get service account credentials
        username, secret = get_service_account_credentials()
        
        # Use Basic Auth with service account credentials
        auth = httpx.BasicAuth(username, secret)
        
        headers = {
            "Content-Type": "application/json"
        }
        
        url = f"{MIXPANEL_APP_ENDPOINT}{endpoint}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method.upper() == "GET":
                response = await client.get(url, auth=auth, headers=headers, params=params)
            elif method.upper() == "POST":
                response = await client.post(url, auth=auth, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            # Handle response
            content_type = response.headers.get("content-type", "")
            
            if "application/json" in content_type:
                return response.json()
            elif response.text:
                try:
                    return response.json()
                except ValueError:
                    return {"data": response.text}
            else:
                return {"success": True}