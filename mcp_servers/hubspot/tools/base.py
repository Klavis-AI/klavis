"""
Base utilities for HubSpot MCP server tools.

This module provides the foundational components for making sanitized
API calls to HubSpot. All external API interactions must go through
the safe_api_call wrapper to ensure proper error handling and
data sanitization.
"""

import logging
import os
from contextvars import ContextVar
from typing import Optional, TypeVar, Callable, Any
from hubspot import HubSpot
from dotenv import load_dotenv

from .errors import (
    KlavisError,
    AuthenticationError,
    sanitize_exception,
    format_error_response
)

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

# Context variable to store the access token for each request
auth_token_context: ContextVar[str] = ContextVar('auth_token')

# Type variable for generic return types
T = TypeVar('T')


def get_auth_token() -> str:
    """Get the authentication token from context."""
    try:
        token = auth_token_context.get()
        if not token:
            # Fallback to environment variable if no token in context
            token = os.getenv("HUBSPOT_ACCESS_TOKEN")
            if not token:
                raise AuthenticationError()
        return token
    except LookupError:
        token = os.getenv("HUBSPOT_ACCESS_TOKEN")
        if not token:
            raise AuthenticationError()
        return token


def get_hubspot_client() -> HubSpot:
    """
    Get HubSpot client with auth token from context.
    
    Raises:
        AuthenticationError: If no valid authentication token is available
    """
    try:
        auth_token = get_auth_token()
        client = HubSpot(access_token=auth_token)
        return client
    except AuthenticationError:
        raise
    except Exception:
        # Don't expose the original exception details
        raise AuthenticationError()


def safe_api_call(
    func: Callable[..., T],
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    **kwargs
) -> T:
    """
    Execute an API call with proper error handling and sanitization.
    
    This wrapper ensures that:
    1. All exceptions from third-party APIs are caught
    2. Raw vendor error messages are NEVER exposed
    3. Only HTTP status codes and Klavis-defined error codes are returned
    
    Args:
        func: The API function to call
        resource_type: Optional resource type for error context (e.g., "contact")
        resource_id: Optional resource ID for error context
        **kwargs: Arguments to pass to the API function
        
    Returns:
        The result of the API call
        
    Raises:
        KlavisError: A sanitized error with no vendor details
    """
    try:
        return func(**kwargs)
    except KlavisError:
        # Already sanitized, re-raise
        raise
    except Exception as e:
        # Sanitize the exception before raising
        raise sanitize_exception(
            exception=e,
            resource_type=resource_type,
            resource_id=resource_id
        )


async def async_safe_api_call(
    func: Callable[..., T],
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    **kwargs
) -> T:
    """
    Execute an async API call with proper error handling and sanitization.
    
    This is the async version of safe_api_call.
    
    Args:
        func: The API function to call (can be sync or async)
        resource_type: Optional resource type for error context
        resource_id: Optional resource ID for error context
        **kwargs: Arguments to pass to the API function
        
    Returns:
        The result of the API call
        
    Raises:
        KlavisError: A sanitized error with no vendor details
    """
    try:
        result = func(**kwargs)
        # Handle coroutines if the function is async
        if hasattr(result, '__await__'):
            return await result
        return result
    except KlavisError:
        # Already sanitized, re-raise
        raise
    except Exception as e:
        # Sanitize the exception before raising
        raise sanitize_exception(
            exception=e,
            resource_type=resource_type,
            resource_id=resource_id
        )
