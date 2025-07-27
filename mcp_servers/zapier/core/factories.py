"""
Factory classes for Zapier MCP Server.

This module contains factory classes that implement the Factory pattern
for creating instances of services, repositories, and clients.
"""

from typing import Dict, Any, Optional, Type
from .interfaces import IService, IRepository, IClient, IValidator, ILogger, ICache
from .base_classes import BaseService, BaseRepository, BaseClient, BaseValidator


class ServiceFactory:
    """
    Factory for creating service instances.
    
    Implements the Factory pattern for service creation with
    dependency injection and configuration management.
    """
    
    def __init__(self):
        """Initialize the service factory."""
        self._service_registry: Dict[str, Type[IService]] = {}
        self._dependencies: Dict[str, Dict[str, Any]] = {}
    
    def register_service(
        self,
        service_name: str,
        service_class: Type[IService],
        dependencies: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a service class with its dependencies.
        
        Args:
            service_name: Name of the service
            service_class: Service class to register
            dependencies: Dependencies for the service
        """
        self._service_registry[service_name] = service_class
        self._dependencies[service_name] = dependencies or {}
    
    def create_service(
        self,
        service_name: str,
        **kwargs
    ) -> IService:
        """
        Create a service instance.
        
        Args:
            service_name: Name of the service to create
            **kwargs: Additional parameters for service creation
            
        Returns:
            Service instance
            
        Raises:
            ValueError: If service is not registered
        """
        if service_name not in self._service_registry:
            raise ValueError(f"Service '{service_name}' is not registered")
        
        service_class = self._service_registry[service_name]
        dependencies = self._dependencies[service_name].copy()
        dependencies.update(kwargs)
        
        return service_class(**dependencies)
    
    def get_registered_services(self) -> list[str]:
        """Get list of registered service names."""
        return list(self._service_registry.keys())
    
    def is_registered(self, service_name: str) -> bool:
        """Check if a service is registered."""
        return service_name in self._service_registry


class RepositoryFactory:
    """
    Factory for creating repository instances.
    
    Implements the Factory pattern for repository creation with
    caching and configuration management.
    """
    
    def __init__(self, cache: Optional[ICache] = None, logger: Optional[ILogger] = None):
        """Initialize the repository factory."""
        self._repository_registry: Dict[str, Type[IRepository]] = {}
        self._dependencies: Dict[str, Dict[str, Any]] = {}
        self._cache = cache
        self._logger = logger
    
    def register_repository(
        self,
        repository_name: str,
        repository_class: Type[IRepository],
        dependencies: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a repository class with its dependencies.
        
        Args:
            repository_name: Name of the repository
            repository_class: Repository class to register
            dependencies: Dependencies for the repository
        """
        self._repository_registry[repository_name] = repository_class
        self._dependencies[repository_name] = dependencies or {}
    
    def create_repository(
        self,
        repository_name: str,
        **kwargs
    ) -> IRepository:
        """
        Create a repository instance.
        
        Args:
            repository_name: Name of the repository to create
            **kwargs: Additional parameters for repository creation
            
        Returns:
            Repository instance
            
        Raises:
            ValueError: If repository is not registered
        """
        if repository_name not in self._repository_registry:
            raise ValueError(f"Repository '{repository_name}' is not registered")
        
        repository_class = self._repository_registry[repository_name]
        dependencies = self._dependencies[repository_name].copy()
        dependencies.update(kwargs)
        
        # Add common dependencies
        if self._logger and 'logger' not in dependencies:
            dependencies['logger'] = self._logger
        
        repository = repository_class(**dependencies)
        
        # Set cache if available
        if self._cache and hasattr(repository, 'set_cache'):
            repository.set_cache(self._cache)
        
        return repository
    
    def get_registered_repositories(self) -> list[str]:
        """Get list of registered repository names."""
        return list(self._repository_registry.keys())
    
    def is_registered(self, repository_name: str) -> bool:
        """Check if a repository is registered."""
        return repository_name in self._repository_registry


class ClientFactory:
    """
    Factory for creating client instances.
    
    Implements the Factory pattern for client creation with
    configuration management and connection pooling.
    """
    
    def __init__(self):
        """Initialize the client factory."""
        self._client_registry: Dict[str, Type[IClient]] = {}
        self._configurations: Dict[str, Dict[str, Any]] = {}
    
    def register_client(
        self,
        client_name: str,
        client_class: Type[IClient],
        configuration: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a client class with its configuration.
        
        Args:
            client_name: Name of the client
            client_class: Client class to register
            configuration: Configuration for the client
        """
        self._client_registry[client_name] = client_class
        self._configurations[client_name] = configuration or {}
    
    def create_client(
        self,
        client_name: str,
        **kwargs
    ) -> IClient:
        """
        Create a client instance.
        
        Args:
            client_name: Name of the client to create
            **kwargs: Additional parameters for client creation
            
        Returns:
            Client instance
            
        Raises:
            ValueError: If client is not registered
        """
        if client_name not in self._client_registry:
            raise ValueError(f"Client '{client_name}' is not registered")
        
        client_class = self._client_registry[client_name]
        configuration = self._configurations[client_name].copy()
        configuration.update(kwargs)
        
        return client_class(**configuration)
    
    def get_registered_clients(self) -> list[str]:
        """Get list of registered client names."""
        return list(self._client_registry.keys())
    
    def is_registered(self, client_name: str) -> bool:
        """Check if a client is registered."""
        return client_name in self._client_registry


class ValidatorFactory:
    """
    Factory for creating validator instances.
    
    Implements the Factory pattern for validator creation with
    validation rule management.
    """
    
    def __init__(self):
        """Initialize the validator factory."""
        self._validator_registry: Dict[str, Type[IValidator]] = {}
        self._validation_rules: Dict[str, Dict[str, Any]] = {}
    
    def register_validator(
        self,
        validator_name: str,
        validator_class: Type[IValidator],
        rules: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a validator class with its validation rules.
        
        Args:
            validator_name: Name of the validator
            validator_class: Validator class to register
            rules: Validation rules for the validator
        """
        self._validator_registry[validator_name] = validator_class
        self._validation_rules[validator_name] = rules or {}
    
    def create_validator(
        self,
        validator_name: str,
        **kwargs
    ) -> IValidator:
        """
        Create a validator instance.
        
        Args:
            validator_name: Name of the validator to create
            **kwargs: Additional parameters for validator creation
            
        Returns:
            Validator instance
            
        Raises:
            ValueError: If validator is not registered
        """
        if validator_name not in self._validator_registry:
            raise ValueError(f"Validator '{validator_name}' is not registered")
        
        validator_class = self._validator_registry[validator_name]
        rules = self._validation_rules[validator_name].copy()
        rules.update(kwargs)
        
        return validator_class(**rules)
    
    def get_registered_validators(self) -> list[str]:
        """Get list of registered validator names."""
        return list(self._validator_registry.keys())
    
    def is_registered(self, validator_name: str) -> bool:
        """Check if a validator is registered."""
        return validator_name in self._validator_registry


class ComponentFactory:
    """
    Master factory for creating all component types.
    
    Implements the Abstract Factory pattern for creating
    services, repositories, clients, and validators.
    """
    
    def __init__(self):
        """Initialize the component factory."""
        self.service_factory = ServiceFactory()
        self.repository_factory = RepositoryFactory()
        self.client_factory = ClientFactory()
        self.validator_factory = ValidatorFactory()
    
    def register_component(
        self,
        component_type: str,
        component_name: str,
        component_class: Type,
        **kwargs
    ) -> None:
        """
        Register a component with the appropriate factory.
        
        Args:
            component_type: Type of component (service, repository, client, validator)
            component_name: Name of the component
            component_class: Component class to register
            **kwargs: Additional parameters for registration
        """
        if component_type == "service":
            self.service_factory.register_service(component_name, component_class, kwargs)
        elif component_type == "repository":
            self.repository_factory.register_repository(component_name, component_class, kwargs)
        elif component_type == "client":
            self.client_factory.register_client(component_name, component_class, kwargs)
        elif component_type == "validator":
            self.validator_factory.register_validator(component_name, component_class, kwargs)
        else:
            raise ValueError(f"Unknown component type: {component_type}")
    
    def create_component(
        self,
        component_type: str,
        component_name: str,
        **kwargs
    ) -> Any:
        """
        Create a component instance.
        
        Args:
            component_type: Type of component to create
            component_name: Name of the component
            **kwargs: Additional parameters for component creation
            
        Returns:
            Component instance
        """
        if component_type == "service":
            return self.service_factory.create_service(component_name, **kwargs)
        elif component_type == "repository":
            return self.repository_factory.create_repository(component_name, **kwargs)
        elif component_type == "client":
            return self.client_factory.create_client(component_name, **kwargs)
        elif component_type == "validator":
            return self.validator_factory.create_validator(component_name, **kwargs)
        else:
            raise ValueError(f"Unknown component type: {component_type}")
    
    def get_registered_components(self, component_type: str) -> list[str]:
        """Get list of registered component names for a type."""
        if component_type == "service":
            return self.service_factory.get_registered_services()
        elif component_type == "repository":
            return self.repository_factory.get_registered_repositories()
        elif component_type == "client":
            return self.client_factory.get_registered_clients()
        elif component_type == "validator":
            return self.validator_factory.get_registered_validators()
        else:
            raise ValueError(f"Unknown component type: {component_type}") 