"""
Klavis standardized error handling for HubSpot MCP server.

This module provides a sanitization layer for third-party API errors.
"""

import logging
import re
from enum import Enum
from typing import Optional, Any
from functools import wraps

logger = logging.getLogger(__name__)


class KlavisErrorCode(str, Enum):
    """Klavis-defined error codes."""
    
    # Authentication & Authorization
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    AUTHORIZATION_DENIED = "AUTHORIZATION_DENIED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    
    # Resource Errors
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    
    # Validation Errors
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    
    # Rate Limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Server Errors
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    
    # Operation Errors
    OPERATION_FAILED = "OPERATION_FAILED"
    OPERATION_TIMEOUT = "OPERATION_TIMEOUT"


class KlavisError(Exception):
    """Base Klavis error class with sanitized information."""
    
    def __init__(
        self,
        code: KlavisErrorCode,
        http_status: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ):
        self.code = code
        self.http_status = http_status
        self.resource_type = resource_type
        self.resource_id = resource_id
        
        # Build sanitized message
        message_parts = [f"Error {code.value}"]
        if http_status:
            message_parts.append(f"(HTTP {http_status})")
        if resource_type:
            message_parts.append(f"for {resource_type}")
        if resource_id:
            message_parts.append(f"ID: {resource_id}")
            
        self.message = " ".join(message_parts)
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        """Convert error to dictionary for JSON serialization."""
        result = {
            "error": True,
            "code": self.code.value,
            "message": self.message
        }
        if self.http_status:
            result["http_status"] = self.http_status
        if self.resource_type:
            result["resource_type"] = self.resource_type
        if self.resource_id:
            result["resource_id"] = self.resource_id
        return result


class AuthenticationError(KlavisError):
    """Authentication-related errors."""
    
    def __init__(self, http_status: Optional[int] = 401):
        super().__init__(
            code=KlavisErrorCode.AUTHENTICATION_FAILED,
            http_status=http_status
        )


class AuthorizationError(KlavisError):
    """Authorization/permission-related errors."""
    
    def __init__(self, http_status: Optional[int] = 403, resource_type: Optional[str] = None):
        super().__init__(
            code=KlavisErrorCode.AUTHORIZATION_DENIED,
            http_status=http_status,
            resource_type=resource_type
        )


class ResourceNotFoundError(KlavisError):
    """Resource not found errors."""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[str] = None,
        http_status: Optional[int] = 404
    ):
        super().__init__(
            code=KlavisErrorCode.RESOURCE_NOT_FOUND,
            http_status=http_status,
            resource_type=resource_type,
            resource_id=resource_id
        )


class ValidationError(KlavisError):
    """Input validation errors."""
    
    def __init__(
        self,
        http_status: Optional[int] = 400,
        resource_type: Optional[str] = None
    ):
        super().__init__(
            code=KlavisErrorCode.INVALID_INPUT,
            http_status=http_status,
            resource_type=resource_type
        )


class RateLimitError(KlavisError):
    """Rate limiting errors."""
    
    def __init__(self, http_status: Optional[int] = 429):
        super().__init__(
            code=KlavisErrorCode.RATE_LIMIT_EXCEEDED,
            http_status=http_status
        )


class ServiceUnavailableError(KlavisError):
    """Service unavailable errors."""
    
    def __init__(self, http_status: Optional[int] = 503):
        super().__init__(
            code=KlavisErrorCode.SERVICE_UNAVAILABLE,
            http_status=http_status
        )


class OperationError(KlavisError):
    """Generic operation failure."""
    
    def __init__(
        self,
        http_status: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ):
        super().__init__(
            code=KlavisErrorCode.OPERATION_FAILED,
            http_status=http_status,
            resource_type=resource_type,
            resource_id=resource_id
        )


def _extract_http_status(exception: Exception) -> Optional[int]:
    """Extract HTTP status code from various exception types."""
    # Check for status_code attribute (common in HTTP clients)
    if hasattr(exception, 'status_code'):
        return getattr(exception, 'status_code')
    
    # Check for status attribute
    if hasattr(exception, 'status'):
        status = getattr(exception, 'status')
        if isinstance(status, int):
            return status
    
    # Check for response.status_code (requests-style)
    if hasattr(exception, 'response'):
        response = getattr(exception, 'response')
        if hasattr(response, 'status_code'):
            return getattr(response, 'status_code')
        if hasattr(response, 'status'):
            return getattr(response, 'status')
    
    # Try to extract from exception string (last resort)
    # Only extract numeric status code, nothing else
    exc_str = str(exception)
    
    # Pattern to match HTTP status codes
    status_patterns = [
        r'(?:status[_\s]?code|http|error)[:\s]*(\d{3})',
        r'\b([45]\d{2})\b',  # Match 4xx or 5xx codes
    ]
    
    for pattern in status_patterns:
        match = re.search(pattern, exc_str, re.IGNORECASE)
        if match:
            try:
                status = int(match.group(1))
                if 100 <= status <= 599:
                    return status
            except ValueError:
                continue
    
    return None


def sanitize_exception(
    exception: Exception,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None
) -> KlavisError:
    """
    Convert any exception to a sanitized KlavisError.
    
    Args:
        exception: The original exception from the third-party API
        resource_type: Optional resource type for context (e.g., "contact", "deal")
        resource_id: Optional resource ID for context
        
    Returns:
        A sanitized KlavisError
    """
    # Log the full exception for debugging
    logger.error(
        f"Third-party API error (sanitized before returning): {type(exception).__name__}",
        exc_info=True
    )
    
    # Extract HTTP status code
    http_status = _extract_http_status(exception)
    
    # If it's already a KlavisError, return as-is
    if isinstance(exception, KlavisError):
        return exception
    
    # Map HTTP status codes to Klavis error types
    if http_status:
        if http_status == 401:
            return AuthenticationError(http_status=http_status)
        elif http_status == 403:
            return AuthorizationError(http_status=http_status, resource_type=resource_type)
        elif http_status == 404:
            return ResourceNotFoundError(
                resource_type=resource_type or "resource",
                resource_id=resource_id,
                http_status=http_status
            )
        elif http_status == 400 or http_status == 422:
            return ValidationError(http_status=http_status, resource_type=resource_type)
        elif http_status == 429:
            return RateLimitError(http_status=http_status)
        elif http_status >= 500:
            return ServiceUnavailableError(http_status=http_status)
        else:
            return OperationError(
                http_status=http_status,
                resource_type=resource_type,
                resource_id=resource_id
            )
    
    # Check exception type names (without exposing vendor-specific messages)
    exc_type = type(exception).__name__.lower()
    
    if 'auth' in exc_type or 'token' in exc_type or 'credential' in exc_type:
        return AuthenticationError()
    elif 'permission' in exc_type or 'forbidden' in exc_type:
        return AuthorizationError(resource_type=resource_type)
    elif 'notfound' in exc_type or 'not_found' in exc_type:
        return ResourceNotFoundError(
            resource_type=resource_type or "resource",
            resource_id=resource_id
        )
    elif 'validation' in exc_type or 'invalid' in exc_type:
        return ValidationError(resource_type=resource_type)
    elif 'ratelimit' in exc_type or 'rate_limit' in exc_type or 'throttl' in exc_type:
        return RateLimitError()
    elif 'timeout' in exc_type:
        return KlavisError(
            code=KlavisErrorCode.OPERATION_TIMEOUT,
            resource_type=resource_type,
            resource_id=resource_id
        )
    elif 'connect' in exc_type or 'unavailable' in exc_type:
        return ServiceUnavailableError()
    
    # Default: generic operation error with no details
    return OperationError(
        resource_type=resource_type,
        resource_id=resource_id
    )


def format_error_response(error: KlavisError) -> str:
    """
    Format a KlavisError as a string suitable for returning to the LLM.
    
    This ensures consistent error formatting across all tool responses.
    """
    return error.message

