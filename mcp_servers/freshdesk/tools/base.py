import os
import json
import logging
from dataclasses import dataclass
from typing import Any, Optional, Dict, cast
from contextvars import ContextVar
from urllib.parse import urlparse

import httpx


logger = logging.getLogger(__name__)


class FreshdeskToolExecutionError(Exception):
    def __init__(self, message: str, developer_message: str = "") -> None:
        super().__init__(message)
        self.developer_message = developer_message


class RetryableToolError(Exception):
    def __init__(self, message: str, additional_prompt_content: str = "", retry_after_ms: int = 1000, developer_message: str = ""):
        super().__init__(message)
        self.additional_prompt_content = additional_prompt_content
        self.retry_after_ms = retry_after_ms
        self.developer_message = developer_message


# Store token (API key) per-request from header `x-auth-token`
auth_token_context: ContextVar[str] = ContextVar("auth_token", default="")


def _get_auth_token() -> str:
    try:
        token = auth_token_context.get()
        if token:
            return token
    except LookupError:
        pass

    env_token = os.getenv("FRESHDESK_API_KEY")
    if not env_token:
        raise FreshdeskToolExecutionError(
            "Authentication required. Provide Freshdesk API key via x-auth-token header or FRESHDESK_API_KEY env var.",
            "Missing Freshdesk API key in context and environment.",
        )
    return env_token


def _get_domain() -> str:
    domain = os.getenv("FRESHDESK_DOMAIN", "").strip()
    if not domain:
        raise FreshdeskToolExecutionError(
            "Freshdesk domain is required. Set FRESHDESK_DOMAIN env var (e.g., 'yourcompany' or 'yourcompany.freshdesk.com' or full URL).",
            "FRESHDESK_DOMAIN is missing.",
        )
    # Normalize: allow full URL with scheme or bare domain or subdomain token
    if domain.startswith("http://") or domain.startswith("https://"):
        parsed = urlparse(domain)
        host = parsed.netloc or parsed.path
        host = host.strip("/")
    else:
        host = domain.strip("/")
    if "." not in host:
        host = f"{host}.freshdesk.com"
    return host


@dataclass
class FreshdeskClient:
    api_key: str
    domain: str
    base_path: str = "/api/v2"
    timeout_seconds: int = 30
    max_retries: int = 3

    def _base_url(self) -> str:
        return f"https://{self.domain}{self.base_path}"

    def _auth(self) -> tuple[str, str]:
        # Freshdesk uses basic auth with API key as username and 'X' as password
        return (self.api_key, "X")

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code < 300:
            return
        
        try:
            data = response.json()
            message = data.get("message") or data.get("description") or f"HTTP {response.status_code} error"
            dev_msg = json.dumps(data)
        except Exception:
            message = f"HTTP {response.status_code} error"
            dev_msg = response.text
        
        # Check for retryable errors
        if response.status_code in [429, 500, 502, 503, 504]:
            raise RetryableToolError(
                message,
                f"Request failed with status {response.status_code}. This may be a temporary issue.",
                2000,  # 2 second retry delay
                dev_msg
            )
        
        raise FreshdeskToolExecutionError(message, dev_msg)

    async def _make_request_with_retry(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Make HTTP request with retry logic for retryable errors."""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds, auth=self._auth()) as client:
                    if method.upper() == "GET":
                        response = await client.get(url, **kwargs)
                    elif method.upper() == "POST":
                        response = await client.post(url, **kwargs)
                    elif method.upper() == "PUT":
                        response = await client.put(url, **kwargs)
                    elif method.upper() == "DELETE":
                        response = await client.delete(url, **kwargs)
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")
                    
                    return response
                    
            except RetryableToolError as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    import asyncio
                    await asyncio.sleep(e.retry_after_ms / 1000)
                    continue
                else:
                    raise
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    import asyncio
                    await asyncio.sleep(1)  # 1 second delay for other errors
                    continue
                else:
                    raise
        
        # If we get here, all retries failed
        if isinstance(last_exception, RetryableToolError):
            raise last_exception
        else:
            raise FreshdeskToolExecutionError(
                f"Request failed after {self.max_retries} attempts",
                f"Last error: {type(last_exception).__name__}: {str(last_exception)}"
            )

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> dict:
        url = f"{self._base_url()}/{endpoint.lstrip('/')}"
        response = await self._make_request_with_retry("GET", url, params=params)
        self._raise_for_status(response)
        return cast(dict, response.json())

    async def post(
        self,
        endpoint: str,
        data: Optional[dict] = None,
        json_data: Optional[dict] = None,
    ) -> dict:
        url = f"{self._base_url()}/{endpoint.lstrip('/')}"
        kwargs: Dict[str, Any] = {}
        if data is not None:
            kwargs["data"] = data
        if json_data is not None:
            kwargs["json"] = json_data
        response = await self._make_request_with_retry("POST", url, **kwargs)
        self._raise_for_status(response)
        return cast(dict, response.json())

    async def put(
        self,
        endpoint: str,
        data: Optional[dict] = None,
        json_data: Optional[dict] = None,
    ) -> dict:
        url = f"{self._base_url()}/{endpoint.lstrip('/')}"
        kwargs: Dict[str, Any] = {}
        if data is not None:
            kwargs["data"] = data
        if json_data is not None:
            kwargs["json"] = json_data
        response = await self._make_request_with_retry("PUT", url, **kwargs)
        self._raise_for_status(response)
        return cast(dict, response.json())

    async def delete(self, endpoint: str) -> dict:
        url = f"{self._base_url()}/{endpoint.lstrip('/')}"
        response = await self._make_request_with_retry("DELETE", url)
        self._raise_for_status(response)
        if response.text:
            try:
                return cast(dict, response.json())
            except Exception:
                return {}
        return {}


def get_freshdesk_client() -> FreshdeskClient:
    token = _get_auth_token()
    domain = _get_domain()
    return FreshdeskClient(api_key=token, domain=domain)


