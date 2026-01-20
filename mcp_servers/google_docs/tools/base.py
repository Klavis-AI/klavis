"""Base utilities for Google Docs MCP Server tools."""

import base64
import json
import logging
import os
from contextvars import ContextVar

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

# Context variable to store the access token for each request
auth_token_context: ContextVar[str] = ContextVar('auth_token')


def extract_access_token(request_or_scope) -> str:
    """Extract access token from x-auth-data header."""
    auth_data = os.getenv("AUTH_DATA")

    if not auth_data:
        # Handle different input types (request object for SSE, scope dict for StreamableHTTP)
        if hasattr(request_or_scope, 'headers'):
            # SSE request object
            auth_data = request_or_scope.headers.get(b'x-auth-data')
            if auth_data:
                auth_data = base64.b64decode(auth_data).decode('utf-8')
        elif isinstance(request_or_scope, dict) and 'headers' in request_or_scope:
            # StreamableHTTP scope object
            headers = dict(request_or_scope.get("headers", []))
            auth_data = headers.get(b'x-auth-data')
            if auth_data:
                auth_data = base64.b64decode(auth_data).decode('utf-8')

    if not auth_data:
        return ""

    try:
        # Parse the JSON auth data to extract access_token
        auth_json = json.loads(auth_data)
        return auth_json.get('access_token', '')
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse auth data JSON: {e}")
        return ""


def get_docs_service(access_token: str):
    """Create Google Docs service with access token."""
    credentials = Credentials(token=access_token)
    return build('docs', 'v1', credentials=credentials)


def get_drive_service(access_token: str):
    """Create Google Drive service with access token."""
    credentials = Credentials(token=access_token)
    return build('drive', 'v3', credentials=credentials)


def get_auth_token() -> str:
    """Get the authentication token from context."""
    try:
        return auth_token_context.get()
    except LookupError:
        raise RuntimeError("Authentication token not found in request context")
