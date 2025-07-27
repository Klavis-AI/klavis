# Zapier MCP Server Architecture

This document outlines the design patterns and architecture used in the Zapier MCP Server.

## Overview

The server follows Clean Architecture principles with three main layers:

- **Core Layer**: Interfaces, base classes, and design patterns
- **Domain Layer**: Business entities and value objects  
- **Infrastructure Layer**: API clients, repositories, and services

## Design Patterns

| Pattern | Purpose | Implementation |
|---------|---------|----------------|
| Factory | Component creation | `ComponentFactory` |
| Repository | Data access | `WorkflowRepository`, `TaskRepository` |
| Service | Business logic | `WorkflowService`, `TaskService` |
| Strategy | Algorithm selection | `WorkflowValidator`, `TaskValidator` |
| Decorator | Cross-cutting concerns | `@retry`, `@cache`, `@log_operation` |

## Project Structure

```
mcp_servers/zapier/
├── core/                    # Design patterns and interfaces
├── domain/                  # Business entities
├── infrastructure/          # API clients, repositories, services
├── tests/                   # Test suite
├── examples/                # Usage examples
├── server.py               # Main server
└── requirements.txt        # Dependencies
```

## Key Features

- **Testable**: Dependency injection and clear interfaces
- **Extensible**: Factory pattern for easy component addition
- **Maintainable**: Single responsibility and clean separation
- **Scalable**: Built-in caching, retry logic, and circuit breaker

## Usage Examples

### Adding a New Service

```python
class TaskService(BaseService[Task]):
    async def _execute_operation(self, operation: str, data: Dict[str, Any]) -> Any:
        # Business logic here
        pass

component_factory.register_component("service", "task", TaskService)
task_service = component_factory.create_component("service", "task")
```

### Adding a New Repository

```python
class TaskRepository(BaseRepository[Task]):
    async def _get_by_id_impl(self, id: str) -> Optional[Task]:
        # Data access logic here
        pass

component_factory.register_component("repository", "task", TaskRepository)
task_repository = component_factory.create_component("repository", "task")
```

## Configuration

The server uses Pydantic Settings for configuration:

```python
# .env file
ZAPIER_API_KEY=your_api_key_here
API_BASE_URL=https://api.zapier.com/v1
API_TIMEOUT=30
LOG_LEVEL=INFO
CACHE_MAX_SIZE=1000
CACHE_TTL=300
```

## Performance Features

- **Caching**: Repository-level caching with configurable TTL
- **Retry Logic**: Exponential backoff with configurable attempts
- **Circuit Breaker**: Prevents cascading failures
- **Rate Limiting**: Built-in request throttling

## Testing

Run tests with:

```bash
python tests/run_tests.py
python tests/run_tests.py --specific interfaces entities
```

## Getting Started

1. Check `examples/design_patterns_demo.py` for usage examples
2. Review `core/` directory for design patterns
3. Examine `infrastructure/` directory for implementations
4. Run the demo to see patterns in action

## Contributing

When contributing:

1. Follow existing design patterns
2. Keep layers properly separated
3. Write comprehensive tests
4. Update documentation for new features 