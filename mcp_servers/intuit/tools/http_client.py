import os
import logging
import httpx
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class QuickBooksHTTPClient:
    """Direct HTTP client for QuickBooks API using httpx library."""
    
    def __init__(self):
        self.access_token = os.getenv('QB_ACCESS_TOKEN')
        self.company_id = os.getenv('QB_REALM_ID')
        self.environment = os.getenv('QB_ENVIRONMENT', 'sandbox').lower()
        self.async_session = httpx.AsyncClient()
        
        if self.environment == 'sandbox':
            self.base_url = "https://sandbox-quickbooks.api.intuit.com"
        else:
            self.base_url = "https://quickbooks.api.intuit.com"
    
    def is_configured(self) -> bool:
        """Check if client is properly configured."""
        return bool(self.access_token and self.company_id)
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to QuickBooks API."""
        if not self.is_configured():
            raise ValueError("QuickBooks client not properly configured")
        
        url = f"{self.base_url}/v3/company/{self.company_id}/{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json'
        }
        
        if 'json' in kwargs:
            headers['Content-Type'] = 'application/json'
            logger.debug(f"Sending {method} request to {url} with data: {kwargs.get('json')}")
        
        try:
            response = await self.async_session.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            
            if response.status_code == 200 and not response.text:
                return {"status": "deleted"}
                
            data = response.json()
            if 'QueryResponse' in data:
                return data['QueryResponse']
            else:
                return data
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Status code: {e.response.status_code}")
                logger.error(f"Response headers: {e.response.headers}")
                try:
                    error_details = e.response.json()
                    logger.error(f"Error details: {error_details}")
                except:
                    logger.error(f"Response text: {e.response.text}")
            raise RuntimeError(f"QuickBooks API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
    
    async def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """GET request."""
        return await self._make_request('GET', endpoint, params=params)
    
    async def _post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """POST request."""
        return await self._make_request('POST', endpoint, json=data)

    async def close(self):
        await self.async_session.aclose()