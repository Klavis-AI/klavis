"""
Interfaces for Zapier MCP Server.

This module defines the interfaces that establish contracts
between different components of the system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
from datetime import datetime

T = TypeVar('T')


class IRepository(ABC, Generic[T]):
    """
    Repository interface for data access operations.
    
    Defines the contract for data access operations following
    the Repository pattern.
    """
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]:
        """Retrieve an entity by its ID."""
        pass
    
    @abstractmethod
    async def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        """Retrieve all entities with optional filtering."""
        pass
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity."""
        pass
    
    @abstractmethod
    async def update(self, id: str, entity: T) -> Optional[T]:
        """Update an existing entity."""
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete an entity by ID."""
        pass
    
    @abstractmethod
    async def exists(self, id: str) -> bool:
        """Check if an entity exists."""
        pass


class IService(ABC, Generic[T]):
    """
    Service interface for business logic operations.
    
    Defines the contract for business logic operations following
    the Service Layer pattern.
    """
    
    @abstractmethod
    async def execute_operation(self, operation: str, data: Dict[str, Any]) -> Any:
        """Execute a business operation."""
        pass
    
    @abstractmethod
    def validate_request(self, data: Dict[str, Any]) -> bool:
        """Validate incoming request data."""
        pass
    
    @abstractmethod
    def create_response(self, data: Any, success: bool = True) -> Dict[str, Any]:
        """Create a standardized response."""
        pass


class IClient(ABC):
    """
    Client interface for external API communication.
    
    Defines the contract for external API communication
    following the Adapter pattern.
    """
    
    @abstractmethod
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GET request."""
        pass
    
    @abstractmethod
    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a POST request."""
        pass
    
    @abstractmethod
    async def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a PUT request."""
        pass
    
    @abstractmethod
    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make a DELETE request."""
        pass
    
    @abstractmethod
    def get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        pass


class IValidator(ABC):
    """
    Validator interface for data validation.
    
    Defines the contract for data validation operations
    following the Strategy pattern.
    """
    
    @abstractmethod
    def validate(self, data: Any) -> bool:
        """Validate the given data."""
        pass
    
    @abstractmethod
    def get_errors(self) -> List[str]:
        """Get validation errors."""
        pass
    
    @abstractmethod
    def clear_errors(self) -> None:
        """Clear validation errors."""
        pass


class ILogger(ABC):
    """
    Logger interface for logging operations.
    
    Defines the contract for logging operations following
    the Strategy pattern.
    """
    
    @abstractmethod
    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message."""
        pass
    
    @abstractmethod
    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message."""
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message."""
        pass
    
    @abstractmethod
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message."""
        pass


class ICache(ABC):
    """
    Cache interface for caching operations.
    
    Defines the contract for caching operations following
    the Strategy pattern.
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in cache."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        pass


class IEventBus(ABC):
    """
    Event bus interface for event-driven operations.
    
    Defines the contract for event-driven operations following
    the Observer pattern.
    """
    
    @abstractmethod
    def subscribe(self, event_type: str, handler: callable) -> None:
        """Subscribe to an event type."""
        pass
    
    @abstractmethod
    def unsubscribe(self, event_type: str, handler: callable) -> None:
        """Unsubscribe from an event type."""
        pass
    
    @abstractmethod
    async def publish(self, event_type: str, data: Any) -> None:
        """Publish an event."""
        pass


class IConfiguration(ABC):
    """
    Configuration interface for application settings.
    
    Defines the contract for configuration management
    following the Singleton pattern.
    """
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """Validate the configuration."""
        pass
    
    @abstractmethod
    def reload(self) -> None:
        """Reload the configuration."""
        pass 