import os
import logging
import httpx
from typing import Dict, Any
from errors import QuickBooksError

logger = logging.getLogger(__name__)


class QuickBooksHTTPClient:
    """Direct HTTP client for QuickBooks API using httpx library."""

    def __init__(self, access_token: str = None, company_id: str = None, environment: str = None, minor_version: int = 75):
        # Use provided parameters or fall back to environment variables
        self.access_token = access_token or os.getenv('QB_ACCESS_TOKEN')
        self.company_id = company_id or os.getenv('QB_REALM_ID')
        self.environment = (environment or os.getenv('QB_ENVIRONMENT', 'production')).lower()
        self.minor_version = minor_version
        self.async_session = httpx.AsyncClient()

        if self.environment == 'sandbox':
            self.base_url = "https://sandbox-quickbooks.api.intuit.com"
        else:
            self.base_url = "https://quickbooks.api.intuit.com"

    def is_configured(self) -> bool:
        """Check if client is properly configured."""
        return bool(self.access_token and self.company_id)

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        if not self.is_configured():
            raise ValueError("QuickBooks client not properly configured")

        url = f"{self.base_url}/v3/company/{self.company_id}/{endpoint}"
        params = kwargs.pop('params', {})
        if params is None:
            params = {}
        params['minorversion'] = self.minor_version

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        logger.debug(
            f"Sending {method} to {url} with data: {kwargs.get('json')}")

        def try_get_resp_json(response):
            try:
                return response.json()
            except Exception:
                return {
                    "error": "Invalid JSON response",
                    "status_code": response.status_code if response else None,
                    "text": response.text,
                }

        try:
            response = await self.async_session.request(
                method, url, headers=headers, params=params, **kwargs
            )
            response.raise_for_status()
            return try_get_resp_json(response)
        except httpx.HTTPStatusError as e:
            logger.error(f"Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Status code: {e.response.status_code}")
                logger.error(f"Response headers: {e.response.headers}")
                logger.error(f"Response text: {e.response.text}")
                resp_json = try_get_resp_json(e.response)
            else:
                resp_json = None
            raise QuickBooksError(
                f"Error: {str(e)}, Status code: {e.response.status_code if e.response else 'N/A'}, Response: {resp_json}",
                original_exception=e,
            )

    async def _get(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """GET request."""
        return await self._make_request('GET', endpoint, params=params)

    async def _post(self, endpoint: str, data: Dict[str, Any], params: Dict[str, Any] = None) -> Dict[str, Any]:
        """POST request."""
        return await self._make_request('POST', endpoint, params=params, json=data)

    async def close(self):
        await self.async_session.aclose()
