import os
from typing import Optional
from contextvars import ContextVar
from notion_client import Client
from notion_client.errors import APIErrorCode

# Context variable to store auth token for the current request
auth_token_context: ContextVar[str] = ContextVar('auth_token', default="")


def get_notion_client() -> Client:
    """Get Notion client with authentication token from context or environment."""
    # Try to get token from context first (for HTTP requests)
    try:
        token = auth_token_context.get()
        if token:
            return Client(auth=token)
    except LookupError:
        pass
    
    # Fall back to environment variable
    token = os.getenv("NOTION_API_KEY")
    if not token:
        raise ValueError("Notion API key not found. Please set NOTION_API_KEY environment variable or provide x-auth-token header.")
    
    return Client(auth=token)


# Notion's SDK raises APIResponseError carrying a structured APIErrorCode and the HTTP
# status, so classification can be exact. Only the three codes below map onto a
# specific category; everything else stays "api_error", which is what the previous
# behaviour already produced for them.
#
# This replaces a substring search over str(error) for "Unauthorized", "Not found" and
# "Forbidden". Notion's messages read "API token is invalid.", "Could not find page
# with ID: ..." and "Insufficient permissions for this endpoint.", so none of those
# three branches could ever match and every failure was reported as a generic
# api_error, including the 404 in issue #1664.
_CODE_TO_TYPE = {
    APIErrorCode.Unauthorized: "authentication_error",
    APIErrorCode.RestrictedResource: "permission_error",
    APIErrorCode.ObjectNotFound: "not_found_error",
}

# Guidance shown to the caller, keyed by category. Kept separate from the vendor's own
# message, which is carried in "details" so the precise text ("Could not find page with
# ID: X") is not thrown away.
_GUIDANCE = {
    "authentication_error": "Authentication failed. Please check your Notion API key.",
    "permission_error": "Access denied. The integration may not have permission to access this resource.",
    "not_found_error": "The requested resource was not found. Check the ID and permissions.",
}


def handle_notion_error(error: Exception) -> dict:
    """Handle Notion API errors and return a structured error envelope.

    The envelope always carries "error" and "type". When the exception comes from the
    Notion SDK it also carries "code" (the vendor's own error code), "status" (the HTTP
    status) and "details" (the vendor's message), so a caller can act on the precise
    failure rather than parse prose.
    """
    code = getattr(error, "code", None)
    error_type = _CODE_TO_TYPE.get(code, "api_error")

    envelope = {
        "error": _GUIDANCE.get(error_type, f"Notion API error: {error}"),
        "type": error_type,
    }

    if code is not None:
        envelope["code"] = code.value if isinstance(code, APIErrorCode) else str(code)

    status = getattr(error, "status", None)
    if isinstance(status, int):
        envelope["status"] = status

    message = str(error)
    if message and message != envelope["error"]:
        envelope["details"] = message

    return envelope



# The four categories handle_notion_error can produce. The dispatch layer has to
# recognise an envelope without re-deriving its shape, so the vocabulary lives here,
# beside the only function that emits it.
ERROR_TYPES = frozenset({
    "authentication_error",
    "not_found_error",
    "permission_error",
    "api_error",
})


def is_error_envelope(value: object) -> bool:
    """Return True if value is an error envelope produced by handle_notion_error.

    Notion payloads carry their own "type" key: a block's type is "paragraph", a
    property's is "rich_text". So "type" alone cannot separate an envelope from a
    real object. The test is deliberately narrow, requiring both keys, a string
    message, and one of the four categories this module emits. A page whose
    user-defined property happens to be named "error" is therefore not misread as
    a failure.
    """
    return (
        isinstance(value, dict)
        and isinstance(value.get("error"), str)
        and value.get("type") in ERROR_TYPES
    )


def validate_uuid(uuid_string: str) -> bool:
    """Validate if a string is a valid UUID format."""
    import re
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(uuid_string))


def format_notion_id(notion_id: str) -> str:
    """Format Notion ID by removing dashes if present."""
    return notion_id.replace('-', '')


def clean_notion_response(response: dict) -> dict:
    """Clean up Notion API response by removing unnecessary fields."""
    if isinstance(response, dict):
        # Remove common unnecessary fields
        cleaned = {k: v for k, v in response.items() 
                  if k not in ['request_id', 'developer_survey']}
        
        # Recursively clean nested dictionaries
        for key, value in cleaned.items():
            if isinstance(value, dict):
                cleaned[key] = clean_notion_response(value)
            elif isinstance(value, list):
                cleaned[key] = [clean_notion_response(item) if isinstance(item, dict) else item 
                              for item in value]
        
        return cleaned
    return response 