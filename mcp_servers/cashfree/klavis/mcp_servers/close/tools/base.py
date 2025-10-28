import asyncio
import json
from dataclasses import dataclass
import logging
from typing import Any, Dict, Optional, cast
from contextvars import ContextVar
from functools import wraps

import httpx

from .constants import CLOSE_API_VERSION, CLOSE_BASE_URL, CLOSE_MAX_CONCURRENT_REQUESTS, CLOSE_MAX_TIMEOUT_SECONDS

# Configure logging
logger = logging.getLogger(__name__)

# Context variable to store the access token for each request
auth_token_context: ContextVar[str] = ContextVar('auth_token')

# Type definitions
ToolResponse = dict[str, Any]

# Exception classes
class ToolExecutionError(Exception):
    def __init__(self, message: str, developer_message: str = ""):
        super().__init__(message)
        self.developer_message = developer_message


class CloseToolExecutionError(ToolExecutionError):
    pass


class PaginationTimeoutError(CloseToolExecutionError):
    def __init__(self, timeout_seconds: int, tool_name: str):
        message = f"Pagination timed out after {timeout_seconds} seconds"
        super().__init__(
            message=message,
            developer_message=f"{message} while calling the tool {tool_name}",
        )


class RetryableToolError(Exception):
    def __init__(self, message: str, additional_prompt_content: str = "", retry_after_ms: int = 1000, developer_message: str = ""):
        super().__init__(message)
        self.additional_prompt_content = additional_prompt_content
        self.retry_after_ms = retry_after_ms
        self.developer_message = developer_message


# Utility functions
def remove_none_values(data: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in data.items() if v is not None}


def format_currency_from_cents(amount_cents: Optional[int], currency: str = "USD") -> Optional[str]:
    """Convert cents to formatted currency string."""
    if amount_cents is None:
        return None
    amount_dollars = amount_cents / 100
    if currency == "USD":
        return f"${amount_dollars:,.2f}"
    return f"{amount_dollars:,.2f} {currency}"


def format_opportunity_values(opportunity: dict[str, Any]) -> dict[str, Any]:
    """Format opportunity monetary values from cents to readable currency strings."""
    formatted_opp = opportunity.copy()
    
    # List of fields that contain monetary values in cents
    money_fields = ['value', 'expected_value', 'annualized_value', 'annualized_expected_value']
    
    for field in money_fields:
        if field in formatted_opp and formatted_opp[field] is not None:
            # Store original value with _cents suffix for reference
            formatted_opp[f"{field}_cents"] = formatted_opp[field]
            # Replace with formatted dollar amount
            currency = formatted_opp.get('value_currency', 'USD')
            formatted_opp[field] = format_currency_from_cents(formatted_opp[field], currency)
    
    return formatted_opp


def format_leads_response(response: dict[str, Any]) -> dict[str, Any]:
    """Format lead response to convert opportunity values from cents to dollars."""
    formatted_response = response.copy()
    
    if 'leads' in formatted_response:
        formatted_leads = []
        for lead in formatted_response['leads']:
            formatted_lead = lead.copy()
            if 'opportunities' in formatted_lead:
                formatted_opportunities = []
                for opp in formatted_lead['opportunities']:
                    formatted_opportunities.append(format_opportunity_values(opp))
                formatted_lead['opportunities'] = formatted_opportunities
            formatted_leads.append(formatted_lead)
        formatted_response['leads'] = formatted_leads
    
    return formatted_response


def get_next_page(response: dict[str, Any]) -> dict[str, Any]:
    """Extract next page information from response."""
    has_more = response.get("has_more", False)
    next_cursor = response.get("next_cursor")
    return {
        "has_more": has_more,
        "next_cursor": next_cursor
    }


# Decorator function to clean Close response
def clean_close_response(func):
    def response_cleaner(data: dict[str, Any]) -> dict[str, Any]:
        # Close API uses 'id' natively, no need to convert like Asana's 'gid'
        # But we can clean up other response format inconsistencies if needed
        
        for k, v in data.items():
            if isinstance(v, dict):
                data[k] = response_cleaner(v)
            elif isinstance(v, list):
                data[k] = [
                    item if not isinstance(item, dict) else response_cleaner(item) for item in v
                ]

        return data

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        response = await func(*args, **kwargs)
        return response_cleaner(response)

    return wrapper


@dataclass
class CloseClient:
    access_token: str
    base_url: str = CLOSE_BASE_URL
    api_version: str = CLOSE_API_VERSION
    max_concurrent_requests: int = CLOSE_MAX_CONCURRENT_REQUESTS
    _semaphore: asyncio.Semaphore | None = None

    def __post_init__(self) -> None:
        self._semaphore = self._semaphore or asyncio.Semaphore(self.max_concurrent_requests)

    def _build_url(self, endpoint: str, api_version: str | None = None) -> str:
        api_version = api_version or self.api_version
        return f"{self.base_url.rstrip('/')}/{api_version.strip('/')}/{endpoint.lstrip('/')}"

    def _build_auth_header(self) -> str:
        """Create Bearer Auth header for Close API."""
        return f"Bearer {self.access_token}"

    def _build_error_messages(self, response: httpx.Response) -> tuple[str, str]:
        try:
            data = response.json()
            
            if "error" in data:
                error_message = data["error"]
                developer_message = f"{error_message} (HTTP status code: {response.status_code})"
            elif "errors" in data:
                errors = data["errors"]
                if len(errors) == 1:
                    error_message = errors[0]
                    developer_message = f"{error_message} (HTTP status code: {response.status_code})"
                else:
                    errors_concat = "', '".join(errors)
                    error_message = f"Multiple errors occurred: '{errors_concat}'"
                    developer_message = f"Multiple errors occurred: {json.dumps(errors)} (HTTP status code: {response.status_code})"
            else:
                error_message = f"HTTP {response.status_code} error"
                developer_message = f"HTTP {response.status_code} error: {response.text}"

        except Exception as e:
            error_message = "Failed to parse Close error response"
            developer_message = f"Failed to parse Close error response: {type(e).__name__}: {e!s}"

        return error_message, developer_message

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code < 300:
            return

        error_message, developer_message = self._build_error_messages(response)

        raise CloseToolExecutionError(error_message, developer_message)

    def _set_request_body(self, kwargs: dict, data: dict | None, json_data: dict | None) -> dict:
        if data and json_data:
            raise ValueError("Cannot provide both data and json_data")

        if data:
            kwargs["data"] = data

        elif json_data:
            kwargs["json"] = json_data

        return kwargs

    @clean_close_response
    async def get(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        api_version: str | None = None,
    ) -> dict:
        default_headers = {
            "Authorization": self._build_auth_header(),
            "Accept": "application/json",
        }
        headers = {**default_headers, **(headers or {})}

        kwargs = {
            "url": self._build_url(endpoint, api_version),
            "headers": headers,
            "timeout": CLOSE_MAX_TIMEOUT_SECONDS,
        }

        if params:
            kwargs["params"] = params

        async with self._semaphore, httpx.AsyncClient() as client:  # type: ignore[union-attr]
            response = await client.get(**kwargs)  # type: ignore[arg-type]
            self._raise_for_status(response)
        return cast(dict, response.json())

    @clean_close_response
    async def post(
        self,
        endpoint: str,
        data: Optional[dict] = None,
        json_data: Optional[dict] = None,
        files: Optional[dict] = None,
        headers: Optional[dict] = None,
        api_version: str | None = None,
    ) -> dict:
        default_headers = {
            "Authorization": self._build_auth_header(),
            "Accept": "application/json",
        }

        if files is None and json_data is not None:
            default_headers["Content-Type"] = "application/json"

        headers = {**default_headers, **(headers or {})}

        kwargs = {
            "url": self._build_url(endpoint, api_version),
            "headers": headers,
            "timeout": CLOSE_MAX_TIMEOUT_SECONDS,
        }

        if files is not None:
            kwargs["files"] = files
            if data is not None:
                kwargs["data"] = data
        else:
            kwargs = self._set_request_body(kwargs, data, json_data)

        async with self._semaphore, httpx.AsyncClient() as client:  # type: ignore[union-attr]
            response = await client.post(**kwargs)  # type: ignore[arg-type]
            self._raise_for_status(response)
        return cast(dict, response.json())

    @clean_close_response
    async def put(
        self,
        endpoint: str,
        data: Optional[dict] = None,
        json_data: Optional[dict] = None,
        headers: Optional[dict] = None,
        api_version: str | None = None,
    ) -> dict:
        headers = headers or {}
        headers["Authorization"] = self._build_auth_header()
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"

        kwargs = {
            "url": self._build_url(endpoint, api_version),
            "headers": headers,
            "timeout": CLOSE_MAX_TIMEOUT_SECONDS,
        }

        kwargs = self._set_request_body(kwargs, data, json_data)

        async with self._semaphore, httpx.AsyncClient() as client:  # type: ignore[union-attr]
            response = await client.put(**kwargs)  # type: ignore[arg-type]
            self._raise_for_status(response)
        return cast(dict, response.json())

    @clean_close_response
    async def delete(
        self,
        endpoint: str,
        headers: Optional[dict] = None,
        api_version: str | None = None,
    ) -> dict:
        headers = headers or {}
        headers["Authorization"] = self._build_auth_header()
        headers["Accept"] = "application/json"

        kwargs = {
            "url": self._build_url(endpoint, api_version),
            "headers": headers,
            "timeout": CLOSE_MAX_TIMEOUT_SECONDS,
        }

        async with self._semaphore, httpx.AsyncClient() as client:  # type: ignore[union-attr]
            response = await client.delete(**kwargs)  # type: ignore[arg-type]
            self._raise_for_status(response)
        
        # Some DELETE responses may be empty
        if response.text:
            return cast(dict, response.json())
        return {}

    async def get_current_user(self) -> dict:
        response = await self.get("/me/")
        return cast(dict, response)


def get_close_client() -> CloseClient:
    access_token = get_auth_token()
    logger.info(f"Access Token: {access_token}")
    return CloseClient(access_token=access_token)


def get_auth_token() -> str:
    """Get the Close access token from the current context."""
    try:
        return auth_token_context.get()
    except LookupError:
        raise CloseToolExecutionError(
            "Authentication required. Please provide a Close access token.",
            "No Close access token found in request context. The access token should be provided in the Authorization header."
        ) 