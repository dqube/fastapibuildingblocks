# Mediator Pattern Implementation

This document describes the mediator pattern implementation in the FastAPI Building Blocks library.

## Overview

The mediator pattern provides a centralized way to handle commands and queries, eliminating the need to inject individual handlers into each endpoint. It acts as a dispatcher that routes requests to their appropriate handlers.

## Architecture

### Core Components

1. **Request** - Base class for all commands and queries
2. **RequestHandler** - Base class for handlers that process requests
3. **IMediator** - Interface defining mediator operations
4. **Mediator** - Implementation that routes requests to handlers
5. **HandlerRegistry** - Registry mapping request types to handlers

### How It Works

```
API Endpoint → Mediator.send(Command/Query) → Handler → Response
```

The mediator:
- Receives a command or query
- Looks up the registered handler for that request type
- Delegates execution to the handler
- Returns the result

## Benefits

### Before Mediator
```python
# Multiple handler dependencies per endpoint
async def create_user(
    user_data: CreateUserDTO,
    create_handler: CreateUserHandlerDep,
) -> SuccessResponse[UserDTO]:
    command = CreateUserCommand(...)
    return await create_handler.handle(command)
```

### After Mediator
```python
# Single mediator dependency
async def create_user(
    user_data: CreateUserDTO,
    mediator: MediatorDep,
) -> SuccessResponse[UserDTO]:
    command = CreateUserCommand(...)
    return await mediator.send(command)
```

**Advantages:**
- ✅ Single dependency injection point
- ✅ Simplified endpoint signatures
- ✅ Consistent request handling pattern
- ✅ Easy to add new commands/queries
- ✅ Better separation of concerns
- ✅ Testability improvements

## Usage

### 1. Define Commands and Queries

Commands and queries automatically inherit from `Request` through the base classes:

```python
from fastapi_building_blocks.application import Command, Query

class CreateUserCommand(Command):
    email: str
    first_name: str
    last_name: str

class GetUserByIdQuery(Query):
    user_id: UUID
```

### 2. Create Handlers

Handlers implement the business logic:

```python
from fastapi_building_blocks.application import CommandHandler

class CreateUserCommandHandler(CommandHandler[UserDTO]):
    def __init__(self, repository: IUserRepository):
        self.repository = repository
    
    async def handle(self, command: CreateUserCommand) -> UserDTO:
        # Business logic here
        user = User.create(...)
        return await self.repository.add(user)
```

### 3. Register Handlers

Register handlers with the mediator using handler factories:

```python
from fastapi_building_blocks.application import Mediator

def get_mediator(repository: UserRepositoryDep) -> IMediator:
    mediator = Mediator()
    
    # Register command handlers
    mediator.register_handler_factory(
        CreateUserCommand,
        lambda: CreateUserCommandHandler(repository)
    )
    
    # Register query handlers
    mediator.register_handler_factory(
        GetUserByIdQuery,
        lambda: GetUserByIdQueryHandler(repository)
    )
    
    return mediator

MediatorDep = Annotated[IMediator, Depends(get_mediator)]
```

### 4. Use in Endpoints

Inject the mediator and send requests:

```python
from fastapi import APIRouter
from fastapi_building_blocks.api.responses import SuccessResponse

router = APIRouter()

@router.post("/users/")
async def create_user(
    user_data: CreateUserDTO,
    mediator: MediatorDep,
) -> SuccessResponse[UserDTO]:
    command = CreateUserCommand(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
    )
    
    user = await mediator.send(command)
    
    return SuccessResponse.create(
        data=user,
        message="User created successfully",
    )
```

## Advanced Features

### Handler Factories vs Static Handlers

**Handler Factories (Recommended):**
```python
# Good for dependency injection per request
mediator.register_handler_factory(
    CreateUserCommand,
    lambda: CreateUserCommandHandler(repository)
)
```

**Static Handlers:**
```python
# Good for stateless handlers
handler = CreateUserCommandHandler(repository)
mediator.register_handler(CreateUserCommand, handler)
```

### Custom Mediator Configuration

For production applications, configure the mediator once at startup:

```python
from fastapi import FastAPI
from fastapi_building_blocks.application import Mediator

def configure_mediator(app: FastAPI) -> Mediator:
    """Configure mediator with all handlers."""
    mediator = Mediator()
    
    # Register all command handlers
    for command_type, handler_factory in get_command_handlers():
        mediator.register_handler_factory(command_type, handler_factory)
    
    # Register all query handlers
    for query_type, handler_factory in get_query_handlers():
        mediator.register_handler_factory(query_type, handler_factory)
    
    return mediator

@app.on_event("startup")
def startup():
    app.state.mediator = configure_mediator(app)

def get_mediator(request: Request) -> IMediator:
    return request.app.state.mediator
```

## Testing

The mediator pattern makes testing easier:

```python
import pytest
from fastapi_building_blocks.application import Mediator

@pytest.fixture
def mediator(mock_repository):
    mediator = Mediator()
    mediator.register_handler_factory(
        CreateUserCommand,
        lambda: CreateUserCommandHandler(mock_repository)
    )
    return mediator

async def test_create_user(mediator):
    command = CreateUserCommand(
        email="test@example.com",
        first_name="John",
        last_name="Doe"
    )
    
    result = await mediator.send(command)
    
    assert result.email == "test@example.com"
    assert result.first_name == "John"
```

## Best Practices

1. **One Handler Per Request Type** - Each command/query should have exactly one handler
2. **Use Handler Factories** - For proper dependency injection and lifecycle management
3. **Keep Handlers Focused** - Each handler should do one thing well
4. **Configure Once** - Set up the mediator at application startup
5. **Type Safety** - Use type hints for better IDE support and error checking
6. **Command/Query Separation** - Keep commands and queries distinct

## Error Handling

The mediator will raise a `ValueError` if no handler is registered:

```python
try:
    result = await mediator.send(UnregisteredCommand())
except ValueError as e:
    # Handle missing handler
    print(f"No handler found: {e}")
```

## Migration Guide

### From Direct Handler Injection

1. Update imports:
   ```python
   # Remove individual handler dependencies
   - from ...dependencies import CreateUserHandlerDep
   # Add mediator dependency
   + from ...dependencies import MediatorDep
   ```

2. Update endpoint signatures:
   ```python
   - handler: CreateUserHandlerDep,
   + mediator: MediatorDep,
   ```

3. Update handler calls:
   ```python
   - result = await handler.handle(command)
   + result = await mediator.send(command)
   ```

## Integration with Existing Code

The mediator pattern is fully compatible with existing commands, queries, and handlers. Commands and queries now inherit from `Request` through their base classes, making them compatible with both:
- Direct handler invocation: `await handler.handle(command)`
- Mediator dispatch: `await mediator.send(command)`

This allows for gradual migration without breaking existing functionality.

## Summary

The mediator pattern provides a clean, scalable way to handle commands and queries in your FastAPI application. It reduces boilerplate, improves testability, and makes it easier to add new features without modifying existing code.
