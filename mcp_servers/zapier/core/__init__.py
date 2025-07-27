"""
Core package for Zapier MCP Server.

This module contains the foundational design patterns, interfaces,
and base classes that form the architecture backbone.
"""

from .interfaces import IRepository, IService, IClient, IValidator
from .base_classes import BaseRepository, BaseService, BaseClient, BaseValidator
from .factories import ServiceFactory, RepositoryFactory, ClientFactory
from .decorators import retry, cache, validate, log_operation
from .exceptions import (
    ValidationError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ServiceError
)

__all__ = [
    # Interfaces
    "IRepository",
    "IService", 
    "IClient",
    "IValidator",
    
    # Base Classes
    "BaseRepository",
    "BaseService",
    "BaseClient", 
    "BaseValidator",
    
    # Factories
    "ServiceFactory",
    "RepositoryFactory",
    "ClientFactory",
    
    # Decorators
    "retry",
    "cache", 
    "validate",
    "log_operation",
    
    # Exceptions
    "ValidationError",
    "AuthenticationError",
    "RateLimitError",
    "NotFoundError",
    "ServiceError",
] 