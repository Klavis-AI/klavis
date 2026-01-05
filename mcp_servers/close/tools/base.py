import asyncio
import json
from dataclasses import dataclass
import logging
from typing import Any, Dict, List, Optional, Callable, Union, cast
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


# ============================================================================
# Response Normalization Utilities (Klavis Interface Layer)
# ============================================================================
# These utilities transform raw API responses into Klavis-defined schemas,

def get_path(data: Dict, path: str) -> Any:
    """Safe dot-notation access. Returns None if path fails."""
    if not data:
        return None
    current = data
    for key in path.split('.'):
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return None
    return current


def normalize(source: Dict, mapping: Dict[str, Any]) -> Dict:
    """
    Creates a new clean dictionary based strictly on the mapping rules.
    Excludes fields with None/null values from the output.
    Args:
        source: Raw API JSON.
        mapping: Dict of { "targetFieldName": "source.path" OR lambda_function }
    """
    clean_data = {}
    for target_key, rule in mapping.items():
        value = None
        if isinstance(rule, str):
            value = get_path(source, rule)
        elif callable(rule):
            try:
                value = rule(source)
            except Exception:
                value = None
        if value is not None:
            clean_data[target_key] = value
    return clean_data


def normalize_list(items: List[Dict], mapping: Dict[str, Any]) -> List[Dict]:
    """Normalize a list of items using the provided mapping."""
    return [normalize(item, mapping) for item in items if item]


# ============================================================================
# Klavis Interface Mapping Rules
# ============================================================================

# Email/Phone nested object rules
EMAIL_RULES = {
    "address": "email",
    "type": "type",
}

PHONE_RULES = {
    "number": "phone",
    "type": "type",
}

URL_RULES = {
    "url": "url",
    "type": "type",
}

ADDRESS_RULES = {
    "line1": "address_1",
    "line2": "address_2",
    "city": "city",
    "state": "state",
    "postalCode": "zipcode",
    "country": "country",
}

# Contact rules
CONTACT_RULES = {
    "id": "id",
    "leadId": "lead_id",
    "name": "name",
    "firstName": "first_name",
    "lastName": "last_name",
    "title": "title",
    "emails": lambda x: normalize_list(x.get("emails", []), EMAIL_RULES) if x.get("emails") else None,
    "phones": lambda x: normalize_list(x.get("phones", []), PHONE_RULES) if x.get("phones") else None,
    "urls": lambda x: normalize_list(x.get("urls", []), URL_RULES) if x.get("urls") else None,
    "createdAt": "date_created",
    "updatedAt": "date_updated",
}

# Lead rules
LEAD_RULES = {
    "id": "id",
    "name": "name",
    "description": "description",
    "statusId": "status_id",
    "statusLabel": "status_label",
    "url": "url",
    "addresses": lambda x: normalize_list(x.get("addresses", []), ADDRESS_RULES) if x.get("addresses") else None,
    "contacts": lambda x: normalize_list(x.get("contacts", []), CONTACT_RULES) if x.get("contacts") else None,
    "createdAt": "date_created",
    "updatedAt": "date_updated",
    "createdBy": "created_by",
    "updatedBy": "updated_by",
}

# Opportunity rules
OPPORTUNITY_RULES = {
    "id": "id",
    "leadId": "lead_id",
    "leadName": "lead_name",
    "contactId": "contact_id",
    "contactName": "contact_name",
    "userId": "user_id",
    "userName": "user_name",
    "statusId": "status_id",
    "statusLabel": "status_label",
    "statusType": "status_type",
    "note": "note",
    "confidence": "confidence",
    "value": "value",
    "valueCurrency": "value_currency",
    "valuePeriod": "value_period",
    "valueFormatted": "value_formatted",
    "expectedValue": "expected_value",
    "annualizedValue": "annualized_value",
    "annualizedExpectedValue": "annualized_expected_value",
    "expectedCloseDate": "date_won",
    "dateLost": "date_lost",
    "createdAt": "date_created",
    "updatedAt": "date_updated",
    "createdBy": "created_by",
    "updatedBy": "updated_by",
}

# Task rules
TASK_RULES = {
    "id": "id",
    "leadId": "lead_id",
    "leadName": "lead_name",
    "assignedTo": "assigned_to",
    "assignedToName": "assigned_to_name",
    "text": "text",
    "dueDate": "date",
    "isComplete": "is_complete",
    "isDateless": "is_dateless",
    "type": "_type",
    "createdAt": "date_created",
    "updatedAt": "date_updated",
}

# User rules
USER_RULES = {
    "id": "id",
    "email": "email",
    "firstName": "first_name",
    "lastName": "last_name",
    "displayName": lambda x: f"{x.get('first_name', '')} {x.get('last_name', '')}".strip() or x.get('email'),
    "image": "image",
    "createdAt": "date_created",
    "updatedAt": "date_updated",
}

# Email Activity rules
EMAIL_ACTIVITY_RULES = {
    "id": "id",
    "leadId": "lead_id",
    "contactId": "contact_id",
    "userId": "user_id",
    "direction": "direction",
    "status": "status",
    "subject": "subject",
    "bodyText": "body_text",
    "bodyHtml": "body_html",
    "sender": "sender",
    "to": "to",
    "cc": "cc",
    "bcc": "bcc",
    "templateId": "template_id",
    "createdAt": "date_created",
    "updatedAt": "date_updated",
    "sentAt": "date_sent",
}

# Call Activity rules
CALL_ACTIVITY_RULES = {
    "id": "id",
    "leadId": "lead_id",
    "contactId": "contact_id",
    "userId": "user_id",
    "direction": "direction",
    "disposition": "disposition",
    "durationSeconds": "duration",
    "phone": "phone",
    "note": "note",
    "recordingUrl": "recording_url",
    "voicemailUrl": "voicemail_url",
    "createdAt": "date_created",
    "updatedAt": "date_updated",
}

# SMS Activity rules
SMS_ACTIVITY_RULES = {
    "id": "id",
    "leadId": "lead_id",
    "contactId": "contact_id",
    "userId": "user_id",
    "direction": "direction",
    "status": "status",
    "text": "text",
    "remotePhone": "remote_phone",
    "localPhone": "local_phone",
    "createdAt": "date_created",
    "updatedAt": "date_updated",
}

# Note Activity rules
NOTE_ACTIVITY_RULES = {
    "id": "id",
    "leadId": "lead_id",
    "userId": "user_id",
    "note": "note",
    "noteHtml": "note_html",
    "createdAt": "date_created",
    "updatedAt": "date_updated",
}

# Meeting Activity rules
MEETING_ATTENDEE_RULES = {
    "contactId": "contact_id",
    "status": "status",
}

MEETING_ACTIVITY_RULES = {
    "id": "id",
    "leadId": "lead_id",
    "userId": "user_id",
    "status": "status",
    "startsAt": "starts_at",
    "endsAt": "ends_at",
    "attendees": lambda x: normalize_list(x.get("attendees", []), MEETING_ATTENDEE_RULES) if x.get("attendees") else None,
    "noteHtml": "user_note_html",
    "outcomeId": "outcome_id",
    "createdAt": "date_created",
    "updatedAt": "date_updated",
}

# WhatsApp Activity rules
WHATSAPP_ATTACHMENT_RULES = {
    "url": "url",
    "filename": "filename",
    "contentType": "content_type",
}

WHATSAPP_ACTIVITY_RULES = {
    "id": "id",
    "leadId": "lead_id",
    "contactId": "contact_id",
    "userId": "user_id",
    "direction": "direction",
    "externalMessageId": "external_whatsapp_message_id",
    "messageMarkdown": "message_markdown",
    "attachments": lambda x: normalize_list(x.get("attachments", []), WHATSAPP_ATTACHMENT_RULES) if x.get("attachments") else None,
    "integrationLink": "integration_link",
    "replyToId": "response_to_id",
    "createdAt": "date_created",
    "updatedAt": "date_updated",
}

# Generic Activity rules (for list_activities)
ACTIVITY_RULES = {
    "id": "id",
    "type": "_type",
    "leadId": "lead_id",
    "userId": "user_id",
    "createdAt": "date_created",
    "updatedAt": "date_updated",
}


# ============================================================================
# Normalization Functions
# ============================================================================

def normalize_lead(raw: Dict) -> Dict:
    """Normalize a single lead response."""
    lead = normalize(raw, LEAD_RULES)
    # Handle nested opportunities
    if raw.get("opportunities"):
        lead["opportunities"] = normalize_list(raw["opportunities"], OPPORTUNITY_RULES)
    return lead


def normalize_contact(raw: Dict) -> Dict:
    """Normalize a single contact response."""
    return normalize(raw, CONTACT_RULES)


def normalize_opportunity(raw: Dict) -> Dict:
    """Normalize a single opportunity response."""
    return normalize(raw, OPPORTUNITY_RULES)


def normalize_task(raw: Dict) -> Dict:
    """Normalize a single task response."""
    return normalize(raw, TASK_RULES)


def normalize_user(raw: Dict) -> Dict:
    """Normalize a single user response."""
    return normalize(raw, USER_RULES)


def normalize_email_activity(raw: Dict) -> Dict:
    """Normalize a single email activity response."""
    return normalize(raw, EMAIL_ACTIVITY_RULES)


def normalize_call_activity(raw: Dict) -> Dict:
    """Normalize a single call activity response."""
    return normalize(raw, CALL_ACTIVITY_RULES)


def normalize_sms_activity(raw: Dict) -> Dict:
    """Normalize a single SMS activity response."""
    return normalize(raw, SMS_ACTIVITY_RULES)


def normalize_note_activity(raw: Dict) -> Dict:
    """Normalize a single note activity response."""
    return normalize(raw, NOTE_ACTIVITY_RULES)


def normalize_meeting_activity(raw: Dict) -> Dict:
    """Normalize a single meeting activity response."""
    return normalize(raw, MEETING_ACTIVITY_RULES)


def normalize_whatsapp_activity(raw: Dict) -> Dict:
    """Normalize a single WhatsApp activity response."""
    return normalize(raw, WHATSAPP_ACTIVITY_RULES)


def normalize_activity(raw: Dict) -> Dict:
    """Normalize a generic activity response."""
    return normalize(raw, ACTIVITY_RULES)


# ============================================================================
# Exception classes
# ============================================================================

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


# ============================================================================
# Utility functions
# ============================================================================

def remove_none_values(data: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in data.items() if v is not None}


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
        params: Optional[dict] = None,
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

        if params:
            kwargs["params"] = params

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