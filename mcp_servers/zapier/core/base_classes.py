"""
Base classes for Zapier MCP Server.

This module contains base classes that implement common functionality
and provide default implementations for interfaces.
"""

import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic, Callable
from datetime import datetime
import functools

from .interfaces import IRepository, IService, IClient, IValidator, ILogger, ICache
from .exceptions import ValidationError, ServiceError


T = TypeVar('T')


class BaseRepository(IRepository[T]):
    """
    Base repository implementation with common CRUD operations.
    
    Provides default implementations for repository operations
    following the Template Method pattern.
    """
    
    def __init__(self, logger: Optional[ILogger] = None):
        """Initialize the base repository."""
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self._cache: Optional[ICache] = None
    
    def set_cache(self, cache: ICache) -> None:
        """Set the cache instance for this repository."""
        self._cache = cache
    
    async def get_by_id(self, id: str) -> Optional[T]:
        """Retrieve an entity by its ID with caching."""
        # Try cache first
        if self._cache:
            cached = await self._cache.get(f"entity:{id}")
            if cached is not None:
                self.logger.debug(f"Cache hit for entity {id}")
                return cached
        
        # Get from data source
        entity = await self._get_by_id_impl(id)
        
        # Cache the result
        if entity and self._cache:
            await self._cache.set(f"entity:{id}", entity, ttl=300)
        
        return entity
    
    async def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        """Retrieve all entities with optional filtering."""
        cache_key = f"entities:{hash(str(filters))}" if filters else "entities:all"
        
        # Try cache first
        if self._cache:
            cached = await self._cache.get(cache_key)
            if cached is not None:
                self.logger.debug(f"Cache hit for entities with filters {filters}")
                return cached
        
        # Get from data source
        entities = await self._get_all_impl(filters)
        
        # Cache the result
        if self._cache:
            await self._cache.set(cache_key, entities, ttl=60)
        
        return entities
    
    async def create(self, entity: T) -> T:
        """Create a new entity."""
        # Validate before creation
        if not await self._validate_entity(entity):
            raise ValidationError("Entity validation failed")
        
        # Create the entity
        created_entity = await self._create_impl(entity)
        
        # Clear cache
        if self._cache:
            await self._cache.delete("entities:all")
        
        self.logger.info(f"Created entity {getattr(created_entity, 'id', 'unknown')}")
        return created_entity
    
    async def update(self, id: str, entity: T) -> Optional[T]:
        """Update an existing entity."""
        # Check if entity exists
        if not await self.exists(id):
            return None
        
        # Validate before update
        if not await self._validate_entity(entity):
            raise ValidationError("Entity validation failed")
        
        # Update the entity
        updated_entity = await self._update_impl(id, entity)
        
        # Clear cache
        if self._cache:
            await self._cache.delete(f"entity:{id}")
            await self._cache.delete("entities:all")
        
        self.logger.info(f"Updated entity {id}")
        return updated_entity
    
    async def delete(self, id: str) -> bool:
        """Delete an entity by ID."""
        # Check if entity exists
        if not await self.exists(id):
            return False
        
        # Delete the entity
        success = await self._delete_impl(id)
        
        # Clear cache
        if success and self._cache:
            await self._cache.delete(f"entity:{id}")
            await self._cache.delete("entities:all")
        
        self.logger.info(f"Deleted entity {id}")
        return success
    
    async def exists(self, id: str) -> bool:
        """Check if an entity exists."""
        return await self._exists_impl(id)
    
    # Abstract methods that must be implemented by subclasses
    @abstractmethod
    async def _get_by_id_impl(self, id: str) -> Optional[T]:
        """Implementation for getting entity by ID."""
        pass
    
    @abstractmethod
    async def _get_all_impl(self, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        """Implementation for getting all entities."""
        pass
    
    @abstractmethod
    async def _create_impl(self, entity: T) -> T:
        """Implementation for creating entity."""
        pass
    
    @abstractmethod
    async def _update_impl(self, id: str, entity: T) -> Optional[T]:
        """Implementation for updating entity."""
        pass
    
    @abstractmethod
    async def _delete_impl(self, id: str) -> bool:
        """Implementation for deleting entity."""
        pass
    
    @abstractmethod
    async def _exists_impl(self, id: str) -> bool:
        """Implementation for checking entity existence."""
        pass
    
    async def _validate_entity(self, entity: T) -> bool:
        """Validate an entity before persistence."""
        # Default implementation - can be overridden
        return True


class BaseService(IService[T]):
    """
    Base service implementation with common business logic operations.
    
    Provides default implementations for service operations
    following the Template Method pattern.
    """
    
    def __init__(self, repository: IRepository[T], logger: Optional[ILogger] = None):
        """Initialize the base service."""
        self.repository = repository
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self._validators: Dict[str, IValidator] = {}
        self._operation_handlers: Dict[str, Callable] = {}
        self._setup_operation_handlers()
    
    def register_validator(self, operation: str, validator: IValidator) -> None:
        """Register a validator for a specific operation."""
        self._validators[operation] = validator
    
    def register_operation_handler(self, operation: str, handler: Callable) -> None:
        """Register a handler for a specific operation."""
        self._operation_handlers[operation] = handler
    
    async def execute_operation(self, operation: str, data: Dict[str, Any]) -> Any:
        """Execute a business operation with validation and error handling."""
        try:
            # Validate request
            if not self.validate_request(data):
                return self.create_response(
                    None, 
                    success=False, 
                    error="Validation failed"
                )
            
            # Get operation handler
            handler = self._operation_handlers.get(operation)
            if not handler:
                return self.create_response(
                    None,
                    success=False,
                    error=f"Unknown operation: {operation}"
                )
            
            # Execute operation
            result = await handler(data)
            
            # Create success response
            return self.create_response(result, success=True)
            
        except Exception as e:
            self.logger.error(f"Operation {operation} failed: {e}")
            return self.create_response(
                None,
                success=False,
                error=str(e)
            )
    
    def validate_request(self, data: Dict[str, Any]) -> bool:
        """Validate incoming request data."""
        # Default implementation - can be overridden
        return isinstance(data, dict)
    
    def create_response(self, data: Any, success: bool = True, error: Optional[str] = None) -> Dict[str, Any]:
        """Create a standardized response."""
        response = {
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        if error:
            response["error"] = error
        
        return response
    
    def _setup_operation_handlers(self) -> None:
        """Setup default operation handlers."""
        self.register_operation_handler("get_by_id", self._get_by_id_handler)
        self.register_operation_handler("get_all", self._get_all_handler)
        self.register_operation_handler("create", self._create_handler)
        self.register_operation_handler("update", self._update_handler)
        self.register_operation_handler("delete", self._delete_handler)
    
    async def _get_by_id_handler(self, data: Dict[str, Any]) -> Optional[T]:
        """Handler for get_by_id operation."""
        entity_id = data.get("id")
        if not entity_id:
            raise ValidationError("Entity ID is required")
        return await self.repository.get_by_id(entity_id)
    
    async def _get_all_handler(self, data: Dict[str, Any]) -> List[T]:
        """Handler for get_all operation."""
        filters = data.get("filters")
        return await self.repository.get_all(filters)
    
    async def _create_handler(self, data: Dict[str, Any]) -> T:
        """Handler for create operation."""
        entity_data = data.get("entity")
        if not entity_data:
            raise ValidationError("Entity data is required")
        
        # Create entity instance (subclasses should override this)
        entity = self._create_entity_instance(entity_data)
        return await self.repository.create(entity)
    
    async def _update_handler(self, data: Dict[str, Any]) -> Optional[T]:
        """Handler for update operation."""
        entity_id = data.get("id")
        entity_data = data.get("entity")
        
        if not entity_id:
            raise ValidationError("Entity ID is required")
        if not entity_data:
            raise ValidationError("Entity data is required")
        
        # Create entity instance (subclasses should override this)
        entity = self._create_entity_instance(entity_data)
        return await self.repository.update(entity_id, entity)
    
    async def _delete_handler(self, data: Dict[str, Any]) -> bool:
        """Handler for delete operation."""
        entity_id = data.get("id")
        if not entity_id:
            raise ValidationError("Entity ID is required")
        return await self.repository.delete(entity_id)
    
    def _create_entity_instance(self, data: Dict[str, Any]) -> T:
        """Create an entity instance from data."""
        # Default implementation - subclasses should override
        raise NotImplementedError("Subclasses must implement _create_entity_instance")


class BaseClient(IClient):
    """
    Base client implementation for external API communication.
    
    Provides default implementations for HTTP operations
    following the Adapter pattern.
    """
    
    def __init__(self, base_url: str, headers: Dict[str, str], timeout: int = 30):
        """Initialize the base client."""
        self.base_url = base_url.rstrip('/')
        self.default_headers = headers
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GET request."""
        return await self._make_request("GET", endpoint, params=params)
    
    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a POST request."""
        return await self._make_request("POST", endpoint, json=data)
    
    async def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a PUT request."""
        return await self._make_request("PUT", endpoint, json=data)
    
    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make a DELETE request."""
        return await self._make_request("DELETE", endpoint)
    
    def get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        return self.default_headers.copy()
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request with error handling."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {**self.get_headers(), **kwargs.get('headers', {})}
        
        try:
            import requests
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                timeout=self.timeout,
                **{k: v for k, v in kwargs.items() if k != 'headers'}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Request failed: {method} {url} - {e}")
            raise


class BaseValidator(IValidator):
    """
    Base validator implementation with common validation logic.
    
    Provides default implementations for validation operations
    following the Strategy pattern.
    """
    
    def __init__(self):
        """Initialize the base validator."""
        self.errors: List[str] = []
    
    def validate(self, data: Any) -> bool:
        """Validate the given data."""
        self.clear_errors()
        return self._validate_impl(data)
    
    def get_errors(self) -> List[str]:
        """Get validation errors."""
        return self.errors.copy()
    
    def clear_errors(self) -> None:
        """Clear validation errors."""
        self.errors.clear()
    
    def add_error(self, error: str) -> None:
        """Add a validation error."""
        self.errors.append(error)
    
    def _validate_impl(self, data: Any) -> bool:
        """Implementation for validation logic."""
        # Default implementation - subclasses should override
        return True 