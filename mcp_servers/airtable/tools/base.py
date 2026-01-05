import logging
import os
from typing import Any, Dict, Optional
from contextvars import ContextVar

import aiohttp
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================
# Response Normalization Utilities
# ============================================================

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


# ============================================================
# Mapping Rules for Airtable Entities
# ============================================================

BASE_RULES = {
    "id": "id",
    "name": "name",
    "accessLevel": "permissionLevel",
}

TABLE_RULES = {
    "id": "id",
    "name": "name",
    "description": "description",
    "primaryFieldId": "primaryFieldId",
}

FIELD_RULES = {
    "id": "id",
    "name": "name",
    "type": "type",
    "description": "description",
    "options": "options",
}

VIEW_RULES = {
    "id": "id",
    "name": "name",
    "type": "type",
}

RECORD_RULES = {
    "id": "id",
    "createdAt": "createdTime",
    "data": "fields",
    "commentCount": "commentCount",
}


def normalize_field(raw_field: Dict) -> Dict:
    """Normalize a single field."""
    return normalize(raw_field, FIELD_RULES)


def normalize_view(raw_view: Dict) -> Dict:
    """Normalize a single view."""
    return normalize(raw_view, VIEW_RULES)


def normalize_table(raw_table: Dict) -> Dict:
    """Normalize a single table with nested fields and views."""
    table = normalize(raw_table, TABLE_RULES)
    if raw_table.get('fields'):
        table['fields'] = [normalize_field(f) for f in raw_table['fields']]
    if raw_table.get('views'):
        table['views'] = [normalize_view(v) for v in raw_table['views']]
    return table


def normalize_record(raw_record: Dict) -> Dict:
    """Normalize a single record."""
    return normalize(raw_record, RECORD_RULES)


def normalize_base(raw_base: Dict) -> Dict:
    """Normalize a single base."""
    return normalize(raw_base, BASE_RULES)


class AirtableValidationError(Exception):
    """Custom exception for Airtable 422 validation errors."""

    pass


load_dotenv()

AIRTABLE_API_BASE = "https://api.airtable.com/v0"

# Context variable to store the access token for each request
auth_token_context: ContextVar[str] = ContextVar('auth_token')

def get_auth_token() -> str:
    """Get the authentication token from context."""
    try:
        token = auth_token_context.get()
        if not token:
            # Fallback to environment variable if no token in context
            token = os.getenv("AIRTABLE_PERSONAL_ACCESS_TOKEN")
            if not token:
                raise RuntimeError("No authentication token available")
        return token
    except LookupError:
        token = os.getenv("AIRTABLE_PERSONAL_ACCESS_TOKEN")
        if not token:
            raise RuntimeError("Authentication token not found in request context or environment")
        return token

def _get_airtable_headers() -> dict:
    """Get the standard headers for Airtable API requests."""
    auth_token = get_auth_token()
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
    }


async def make_airtable_request(
    method: str,
    endpoint: str,
    json_data: Optional[dict] = None,
    expect_empty_response: bool = False,
) -> dict | None:
    """Make a request to the Airtable API."""
    url = f"{AIRTABLE_API_BASE}/{endpoint}"
    headers = _get_airtable_headers()
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.request(method, url, json=json_data) as response:
                # Handle 422 validation errors specially
                if response.status == 422:
                    error_text = await response.text()
                    logger.error(f"Airtable API 422 Error: {error_text}")
                    raise AirtableValidationError(
                        "Invalid Request body: You may have missed a required field or provided an invalid field. Please check the Airtable Field model for the correct field types and options."
                    )
                response.raise_for_status()  # Raise exception for non-2xx status codes
                if expect_empty_response:
                    # For requests like DELETE or PUT roles/reactions where success is 204 No Content
                    if response.status == 204:
                        return None
                    else:
                        # If we expected empty but got something else (and it wasn't an error raised above)
                        logger.warning(
                            f"Expected empty response for {method} {endpoint}, but got status {response.status}"
                        )
                        # Try to parse JSON anyway, might be useful error info
                        try:
                            return await response.json()
                        except aiohttp.ContentTypeError:
                            return await response.text()  # Return text if not json
                else:
                    # Check if response is JSON before parsing
                    if "application/json" in response.headers.get("Content-Type", ""):
                        return await response.json()
                    else:
                        # Handle non-JSON responses if necessary, e.g., log or return text
                        text_content = await response.text()
                        logger.warning(
                            f"Received non-JSON response for {method} {endpoint}: {text_content[:100]}..."
                        )
                        return {"raw_content": text_content}
        except AirtableValidationError as e:
            # Re-raise 422 validation errors with their specific message
            raise e
        except aiohttp.ClientResponseError as e:
            logger.error(
                f"Airtable API request failed: {e.status} {e.message} for {method} {url}"
            )
            error_details = e.message
            try:
                # Airtable often returns JSON errors
                error_body = await e.response.json()
                error_details = f"{e.message} - {error_body}"
            except Exception:
                # If response body isn't JSON or can't be read
                pass
            raise RuntimeError(
                f"Airtable API Error ({e.status}): {error_details}"
            ) from e
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during Airtable API request: {e}"
            )
            raise RuntimeError(
                f"Unexpected error during API call to {method} {url}"
            ) from e
