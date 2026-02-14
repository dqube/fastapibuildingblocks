# GitHub Copilot Instructions - FastAPI Building Blocks

## Project Context

This is a **FastAPI Building Blocks** library implementing Clean Architecture with DDD principles for enterprise Python applications.

- **Language**: Python 3.12+
- **Framework**: FastAPI with async/await
- **Architecture**: Clean Architecture + Domain-Driven Design
- **Patterns**: CQRS, Repository, Mediator, Inbox/Outbox, Circuit Breaker

## Core Architectural Rules

### Clean Architecture Layers (STRICT)

```
API Layer (Outer)
    ↓ depends on
Infrastructure Layer
    ↓ depends on
Application Layer
    ↓ depends on
Domain Layer (Inner - no external dependencies)
```

**CRITICAL**: Inner layers NEVER depend on outer layers.

### Project Structure

```
src/building_blocks/          # Library code
├── api/                      # Exception handlers, responses
├── application/              # Mediator, commands, queries, handlers
├── domain/                   # Entities, events, repository interfaces
├── infrastructure/           # DB, cache, HTTP, messaging implementations
└── observability/            # Logging, tracing, metrics

example_service/              # Reference implementation
├── app/
│   ├── api/v1/              # Versioned API routes
│   ├── application/         # Commands, queries, handlers, DTOs
│   ├── core/                # Config, database
│   ├── domain/              # Business entities, events, models
│   └── infrastructure/      # Repository implementations

examples/                     # Demo scripts & integration tests
tests/                        # Unit tests
docs/                         # Documentation
```

## Mandatory Code Patterns

### 1. Always Use Async/Await

```python
# ✅ CORRECT
async def get_user(user_id: int, db: AsyncSession) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

# ❌ WRONG - No sync code for I/O operations
def get_user(user_id: int, db: Session) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()
```

### 2. Always Use Type Hints

```python
# ✅ CORRECT
from typing import Optional, List
from datetime import datetime

async def create_user(
    name: str,
    email: str,
    db: AsyncSession
) -> UserDto:
    ...

# ❌ WRONG - Missing type hints
async def create_user(name, email, db):
    ...
```

### 3. Mediator Pattern (CQRS)

**Commands** mutate state, **Queries** read state.

```python
# Command
@dataclass
class CreateUserCommand:
    name: str
    email: str

# Handler
class CreateUserCommandHandler(IRequestHandler[CreateUserCommand, UserDto]):
    def __init__(self, repository: IUserRepository):
        self._repository = repository
    
    async def handle(self, request: CreateUserCommand) -> UserDto:
        user = User(name=request.name, email=request.email)
        await self._repository.add(user)
        return UserDto.from_entity(user)

# API Usage
@router.post("/users", response_model=UserResponse)
async def create_user(
    request: CreateUserRequest,
    mediator: Mediator = Depends(get_mediator)
):
    command = CreateUserCommand(name=request.name, email=request.email)
    result = await mediator.send(command)
    return result
```

### 4. Repository Pattern

**Interface in Domain**:
```python
# domain/repositories/user_repository.py
from abc import ABC, abstractmethod

class IUserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        pass
    
    @abstractmethod
    async def add(self, user: User) -> None:
        pass
```

**Implementation in Infrastructure**:
```python
# infrastructure/repositories/user_repository.py
class UserRepository(IUserRepository):
    def __init__(self, db: AsyncSession):
        self._db = db
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self._db.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def add(self, user: User) -> None:
        db_user = UserModel(**user.dict())
        self._db.add(db_user)
        await self._db.flush()
```

## Technology Stack Guidelines

### FastAPI

```python
# Use APIRouter for modularity
router = APIRouter(prefix="/users", tags=["users"])

# Version APIs
@router.get("/{id}", response_model=UserResponse)
async def get_user(
    id: int,
    mediator: Mediator = Depends(get_mediator)
):
    query = GetUserQuery(user_id=id)
    return await mediator.send(query)
```

### Pydantic v2

```python
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict

class UserDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    created_at: datetime
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        return v.lower()
```

### SQLAlchemy (Async)

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Always use async session and await
async with AsyncSession(engine) as session:
    result = await session.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    await session.commit()
```

### Redis (Async)

```python
import redis.asyncio as redis

class RedisCache:
    def __init__(self, config: RedisConfig):
        self._client = redis.Redis(
            host=config.host,
            port=config.port,
            decode_responses=True
        )
    
    async def get(self, key: str) -> Optional[str]:
        return await self._client.get(key)
    
    async def set(self, key: str, value: str, ttl: int = 300) -> None:
        await self._client.setex(key, ttl, value)
    
    async def execute_lua(self, script: str, keys: List[str], args: List[str]) -> Any:
        lua_script = self._client.register_script(script)
        return await lua_script(keys=keys, args=args)
```

### HTTP Client (httpx)

```python
from building_blocks.infrastructure.http import HttpClient, HttpClientConfig, BearerAuth

# Always use async context manager
client_config = HttpClientConfig(
    base_url="https://api.example.com",
    auth_strategy=BearerAuth(token="xxx"),
    timeout=30.0,
    enable_circuit_breaker=True
)

async with HttpClient(client_config) as client:
    response = await client.get("/users")
    data = response.json()
```

## Error Handling

### Global Exception Handler (RFC 7807)

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(UserNotFoundException)
async def user_not_found_handler(request: Request, exc: UserNotFoundException):
    return JSONResponse(
        status_code=404,
        content={
            "type": "/errors/user-not-found",
            "title": "User Not Found",
            "status": 404,
            "detail": f"User {exc.user_id} not found",
            "instance": str(request.url)
        }
    )
```

### Custom Domain Exceptions

```python
# domain/exceptions.py
class UserNotFoundException(Exception):
    def __init__(self, user_id: int):
        self.user_id = user_id
        super().__init__(f"User {user_id} not found")

class ValidationError(Exception):
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")
```

## Observability

### Structured Logging (ALWAYS Redact Sensitive Data)

```python
import logging

logger = logging.getLogger(__name__)

# ✅ CORRECT - Sensitive data will be auto-redacted
logger.info(
    "User created",
    extra={
        "user_id": user.id,
        "email": user.email,  # Auto-redacted if in sensitive list
        "correlation_id": correlation_id,
        "trace_id": trace_id
    }
)

# ❌ NEVER log passwords, tokens, API keys directly
logger.info(f"User logged in with password: {password}")  # WRONG!
```

### OpenTelemetry Tracing

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def create_user(command: CreateUserCommand) -> UserDto:
    with tracer.start_as_current_span("create_user") as span:
        span.set_attribute("user.email", command.email)
        span.set_attribute("operation", "create")
        
        user = await self._repository.add(user)
        
        span.set_attribute("user.id", user.id)
        return UserDto.from_entity(user)
```

## Dependency Injection

```python
# api/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        yield session

def get_user_repository(
    db: AsyncSession = Depends(get_db)
) -> IUserRepository:
    return UserRepository(db)

def get_mediator(
    db: AsyncSession = Depends(get_db)
) -> Mediator:
    user_repo = UserRepository(db)
    mediator = Mediator()
    
    # Register handlers
    mediator.register(CreateUserCommand, CreateUserCommandHandler(user_repo))
    mediator.register(GetUserQuery, GetUserQueryHandler(user_repo))
    
    return mediator

# Usage in routes
@router.post("/users")
async def create_user(
    request: CreateUserRequest,
    mediator: Mediator = Depends(get_mediator)
):
    command = CreateUserCommand(**request.dict())
    return await mediator.send(command)
```

## File Naming & Organization

### Naming Conventions

- **Modules**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/Variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: `_leading_underscore`

### File Structure

```
application/
├── commands/
│   ├── create_user.py          # CreateUserCommand + Handler
│   └── update_user.py          # UpdateUserCommand + Handler
├── queries/
│   ├── get_user.py             # GetUserQuery + Handler
│   └── list_users.py           # ListUsersQuery + Handler
├── dtos.py                     # All DTOs
└── handlers/                   # Optional: separate handlers

domain/
├── entities/
│   └── user.py                 # User entity
├── events/
│   └── user_events.py          # UserCreatedEvent, etc.
└── repositories/
    └── user_repository.py      # IUserRepository interface

infrastructure/
└── repositories/
    └── user_repository.py      # UserRepository implementation
```

## API Design Standards

### RESTful Endpoints

```python
GET    /api/v1/users              # List all users
GET    /api/v1/users/{id}         # Get specific user
POST   /api/v1/users              # Create user
PUT    /api/v1/users/{id}         # Full update
PATCH  /api/v1/users/{id}         # Partial update
DELETE /api/v1/users/{id}         # Delete user
```

### Request/Response Models

```python
# Request
class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)

# Response
class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
```

### Error Responses (RFC 7807)

```json
{
  "type": "/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "Request validation failed",
  "instance": "/api/v1/users",
  "errors": {
    "email": ["Invalid email format"],
    "password": ["Password must be at least 8 characters"]
  }
}
```

## Testing Guidelines

### Unit Tests

```python
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_create_user_command_handler():
    # Arrange
    mock_repo = Mock(spec=IUserRepository)
    mock_repo.add = AsyncMock()
    handler = CreateUserCommandHandler(mock_repo)
    command = CreateUserCommand(name="John", email="john@example.com")
    
    # Act
    result = await handler.handle(command)
    
    # Assert
    assert result.name == "John"
    assert result.email == "john@example.com"
    mock_repo.add.assert_called_once()
```

### Test Naming

```python
# Pattern: test_<functionality>_<scenario>_<expected_result>
def test_create_user_with_valid_data_returns_user_dto():
    pass

def test_create_user_with_duplicate_email_raises_exception():
    pass

def test_get_user_with_invalid_id_returns_none():
    pass
```

## Configuration

### Settings with Pydantic

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Application
    app_name: str = "My Service"
    environment: str = "development"
    
    # Database
    database_url: str
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    
    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    
    # OpenTelemetry
    otel_service_name: str
    otel_exporter_otlp_endpoint: str
```

## Import Organization

```python
# 1. Standard library
import os
from datetime import datetime
from typing import Optional, List, Dict

# 2. Third-party packages
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

# 3. Local application - building_blocks
from building_blocks.application.mediator import Mediator
from building_blocks.domain.entities import BaseEntity
from building_blocks.infrastructure.cache import RedisCache

# 4. Local application - current service
from app.core.database import get_db
from app.domain.entities import User
from app.application.commands import CreateUserCommand
```

## Key Patterns to Remember

### 1. Context Managers for Resources

```python
# HTTP Client
async with HttpClient(config) as client:
    response = await client.get("/endpoint")

# Database Session
async with AsyncSession(engine) as session:
    result = await session.execute(query)
    await session.commit()

# Redis Connection
async with redis_client.pipeline() as pipe:
    await pipe.set("key1", "value1")
    await pipe.set("key2", "value2")
    await pipe.execute()
```

### 2. Domain Events

```python
# Define in domain/events
@dataclass
class UserCreatedEvent:
    user_id: int
    email: str
    created_at: datetime

# Publish in handler
event = UserCreatedEvent(
    user_id=user.id,
    email=user.email,
    created_at=datetime.utcnow()
)
await event_publisher.publish(event)
```

### 3. Inbox/Outbox Pattern

```python
# Configuration
outbox_config = OutboxConfig(
    enabled=True,
    table_name="outbox_events",
    polling_interval=1.0,
    batch_size=100
)

# Events published within transaction
async with session.begin():
    user = await repository.add(user)
    await outbox.store(UserCreatedEvent(user_id=user.id))
    await session.commit()
```

## Critical Anti-Patterns to AVOID

❌ **DON'T** violate layer dependencies (inner depends on outer)
❌ **DON'T** use sync code for I/O operations
❌ **DON'T** omit type hints
❌ **DON'T** catch exceptions without handling them properly
❌ **DON'T** use mutable default arguments
❌ **DON'T** log sensitive data (passwords, tokens, keys)
❌ **DON'T** return database models directly from API (use DTOs)
❌ **DON'T** put business logic in API route handlers
❌ **DON'T** hardcode configuration values
❌ **DON'T** use blocking I/O in async functions

## Code Generation Checklist

When generating code, ensure:

- [ ] Correct layer placement (Domain → Application → Infrastructure → API)
- [ ] All I/O operations are async/await
- [ ] Complete type hints on all functions/methods
- [ ] Proper exception handling
- [ ] Dependencies injected via FastAPI `Depends()`
- [ ] Sensitive data redaction in logs
- [ ] Pydantic models for validation
- [ ] Repository pattern for data access
- [ ] Mediator pattern for commands/queries
- [ ] OpenTelemetry tracing for important operations
- [ ] Unit tests included
- [ ] Docstrings with examples

## Quick Reference

### New Feature Implementation Order

1. **Domain** → Define entities, events, repository interfaces
2. **Application** → Create commands/queries and handlers
3. **Infrastructure** → Implement repositories, external services
4. **API** → Create routes, request/response models
5. **Tests** → Unit tests, then integration tests
6. **Documentation** → Update docs, add examples

### Technology Versions

- Python: 3.12+
- FastAPI: 0.104+
- SQLAlchemy: 2.0+ (async)
- Pydantic: 2.0+
- Redis: redis-py 5.0+ (asyncio)
- Kafka: aiokafka 0.8+

---

**Remember**: This project prioritizes maintainability, testability, and scalability. Always follow Clean Architecture principles and write async-first code.
