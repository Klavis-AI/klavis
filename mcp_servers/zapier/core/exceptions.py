"""
Custom exceptions for Zapier MCP Server.

This module contains custom exception classes that provide
proper error categorization and handling.
"""

from typing import Any, Dict, Optional


class ZapierError(Exception):
    """
    Base exception for all Zapier MCP Server errors.
    
    Provides common functionality for all custom exceptions
    in the application.
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None
    ):
        """
        Initialize the exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error details
            status_code: HTTP status code if applicable
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.status_code = status_code
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format."""
        return {
            "error": self.message,
            "error_code": self.error_code,
            "details": self.details,
            "status_code": self.status_code,
            "exception_type": self.__class__.__name__
        }


class ValidationError(ZapierError):
    """
    Exception raised when validation fails.
    
    Used for input validation errors, data format issues,
    and business rule violations.
    """
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs
    ):
        """Initialize validation error."""
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = value
        
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            status_code=400,
            **kwargs
        )


class AuthenticationError(ZapierError):
    """
    Exception raised when authentication fails.
    
    Used for API key issues, token expiration,
    and authorization problems.
    """
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        """Initialize authentication error."""
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401,
            **kwargs
        )


class AuthorizationError(ZapierError):
    """
    Exception raised when authorization fails.
    
    Used for permission issues, access control problems,
    and insufficient privileges.
    """
    
    def __init__(self, message: str = "Authorization failed", **kwargs):
        """Initialize authorization error."""
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403,
            **kwargs
        )


class NotFoundError(ZapierError):
    """
    Exception raised when a resource is not found.
    
    Used for missing entities, invalid IDs,
    and resource lookup failures.
    """
    
    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        **kwargs
    ):
        """Initialize not found error."""
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        
        super().__init__(
            message=message,
            error_code="NOT_FOUND_ERROR",
            details=details,
            status_code=404,
            **kwargs
        )


class RateLimitError(ZapierError):
    """
    Exception raised when rate limits are exceeded.
    
    Used for API rate limiting, throttling,
    and request frequency violations.
    """
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs
    ):
        """Initialize rate limit error."""
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            details=details,
            status_code=429,
            **kwargs
        )


class ServiceError(ZapierError):
    """
    Exception raised when service operations fail.
    
    Used for business logic errors, service unavailability,
    and operational failures.
    """
    
    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        """Initialize service error."""
        details = {}
        if service_name:
            details["service_name"] = service_name
        if operation:
            details["operation"] = operation
        
        super().__init__(
            message=message,
            error_code="SERVICE_ERROR",
            details=details,
            status_code=500,
            **kwargs
        )


class ConfigurationError(ZapierError):
    """
    Exception raised when configuration is invalid.
    
    Used for missing environment variables, invalid settings,
    and configuration validation failures.
    """
    
    def __init__(
        self,
        message: str = "Configuration error",
        setting: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs
    ):
        """Initialize configuration error."""
        details = {}
        if setting:
            details["setting"] = setting
        if value is not None:
            details["value"] = value
        
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details,
            status_code=500,
            **kwargs
        )


class NetworkError(ZapierError):
    """
    Exception raised when network operations fail.
    
    Used for connection issues, timeout errors,
    and network-related failures.
    """
    
    def __init__(
        self,
        message: str = "Network error",
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        **kwargs
    ):
        """Initialize network error."""
        details = {}
        if url:
            details["url"] = url
        if status_code:
            details["status_code"] = status_code
        
        super().__init__(
            message=message,
            error_code="NETWORK_ERROR",
            details=details,
            status_code=status_code or 500,
            **kwargs
        )


class CacheError(ZapierError):
    """
    Exception raised when cache operations fail.
    
    Used for cache connection issues, serialization errors,
    and cache-related failures.
    """
    
    def __init__(
        self,
        message: str = "Cache error",
        operation: Optional[str] = None,
        key: Optional[str] = None,
        **kwargs
    ):
        """Initialize cache error."""
        details = {}
        if operation:
            details["operation"] = operation
        if key:
            details["key"] = key
        
        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            details=details,
            status_code=500,
            **kwargs
        )


class SerializationError(ZapierError):
    """
    Exception raised when serialization/deserialization fails.
    
    Used for JSON parsing errors, data format issues,
    and serialization-related failures.
    """
    
    def __init__(
        self,
        message: str = "Serialization error",
        data_type: Optional[str] = None,
        **kwargs
    ):
        """Initialize serialization error."""
        details = {}
        if data_type:
            details["data_type"] = data_type
        
        super().__init__(
            message=message,
            error_code="SERIALIZATION_ERROR",
            details=details,
            status_code=500,
            **kwargs
        )


class TimeoutError(ZapierError):
    """
    Exception raised when operations timeout.
    
    Used for request timeouts, operation timeouts,
    and timeout-related failures.
    """
    
    def __init__(
        self,
        message: str = "Operation timed out",
        timeout_seconds: Optional[float] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        """Initialize timeout error."""
        details = {}
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds
        if operation:
            details["operation"] = operation
        
        super().__init__(
            message=message,
            error_code="TIMEOUT_ERROR",
            details=details,
            status_code=408,
            **kwargs
        )


class CircuitBreakerError(ZapierError):
    """
    Exception raised when circuit breaker is open.
    
    Used for circuit breaker pattern implementation,
    preventing cascading failures.
    """
    
    def __init__(
        self,
        message: str = "Circuit breaker is open",
        service_name: Optional[str] = None,
        failure_count: Optional[int] = None,
        **kwargs
    ):
        """Initialize circuit breaker error."""
        details = {}
        if service_name:
            details["service_name"] = service_name
        if failure_count:
            details["failure_count"] = failure_count
        
        super().__init__(
            message=message,
            error_code="CIRCUIT_BREAKER_ERROR",
            details=details,
            status_code=503,
            **kwargs
        )


# Exception mapping for HTTP status codes
HTTP_STATUS_EXCEPTIONS = {
    400: ValidationError,
    401: AuthenticationError,
    403: AuthorizationError,
    404: NotFoundError,
    408: TimeoutError,
    429: RateLimitError,
    500: ServiceError,
    503: CircuitBreakerError
}


def create_exception_from_status_code(
    status_code: int,
    message: Optional[str] = None,
    **kwargs
) -> ZapierError:
    """
    Create an appropriate exception based on HTTP status code.
    
    Args:
        status_code: HTTP status code
        message: Error message
        **kwargs: Additional exception parameters
        
    Returns:
        Appropriate exception instance
        
    Raises:
        ValueError: If status code is not supported
    """
    if status_code not in HTTP_STATUS_EXCEPTIONS:
        raise ValueError(f"Unsupported status code: {status_code}")
    
    exception_class = HTTP_STATUS_EXCEPTIONS[status_code]
    return exception_class(message or f"HTTP {status_code} error", **kwargs) 