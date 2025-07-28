"""
Base utilities for Zapier MCP Server tools.
"""

from contextvars import ContextVar
from typing import Optional

# Context variable for authentication token
auth_token_context: ContextVar[str] = ContextVar("auth_token", default="")


def get_auth_token() -> Optional[str]:
    """Get the current authentication token from context."""
    token = auth_token_context.get()
    return token if token else None


def require_auth_token() -> str:
    """Get the authentication token, raising an error if not available."""
    token = get_auth_token()
    if not token:
        raise ValueError("Authentication token is required but not provided")
    return token 