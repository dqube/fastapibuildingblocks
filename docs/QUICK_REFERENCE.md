# FastAPI Building Blocks - Quick Reference

A quick reference guide for common patterns, commands, and code snippets.

## 🚀 Common Commands

### Setup & Installation
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install package
pip install -e .            # Development mode
pip install -e ".[dev]"     # With dev dependencies

# Start services
cd example_service
docker-compose up -d        # All services
docker-compose up -d postgres redis  # Specific services
```

### Running & Testing
```bash
# Run example service
cd example_service
docker-compose up           # With logs
docker-compose up -d        # Detached

# Run tests
pytest                      # All tests
pytest tests/               # Unit tests only
pytest examples/            # Integration tests
pytest -v                   # Verbose
pytest --cov=src            # With coverage

# Run specific example
python examples/demo_http_client.py
```

### Code Quality
```bash
# Format code
black .
isort .

# Lint
flake8

# Type check
mypy src/

# All checks
black . && isort . && flake8 && mypy src/ && pytest
```

### Docker
```bash
# View logs
docker-compose logs -f              # All services
docker-compose logs -f api          # Specific service

# Restart services
docker-compose restart api
docker-compose down && docker-compose up -d

# Execute commands in container
docker exec user-management-api python script.py
docker exec -it postgres-db psql -U postgres
```

## 📝 Code Patterns

### 1. Command/Query (CQRS)

**Command (Mutates State)**
```python
from dataclasses import dataclass
from building_blocks.application.mediator import IRequestHandler

@dataclass
class CreateUserCommand:
    name: str
    email: str
    password: str

class CreateUserCommandHandler(IRequestHandler[CreateUserCommand, UserDto]):
    def __init__(self, repository: IUserRepository):
        self._repository = repository
    
    async def handle(self, request: CreateUserCommand) -> UserDto:
        user = User(name=request.name, email=request.email)
        await self._repository.add(user)
        return UserDto.from_entity(user)
```

**Query (Reads State)**
```python
@dataclass
class GetUserQuery:
    user_id: int

class GetUserQueryHandler(IRequestHandler[GetUserQuery, UserDto]):
    async def handle(self, request: GetUserQuery) -> UserDto:
        user = await self._repository.get_by_id(request.user_id)
        if not user:
            raise UserNotFoundException(request.user_id)
        return UserDto.from_entity(user)
```

### 2. API Endpoint

```python
from fastapi import APIRouter, Depends, HTTPException, status
from building_blocks.application.mediator import Mediator

router = APIRouter()

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequest,
    mediator: Mediator = Depends(get_mediator)
) -> UserResponse:
    """Create a new user."""
    command = CreateUserCommand(**request.model_dump())
    result = await mediator.send(command)
    return UserResponse.model_validate(result)

@router.get("/{id}", response_model=UserResponse)
async def get_user(
    id: int,
    mediator: Mediator = Depends(get_mediator)
) -> UserResponse:
    """Get user by ID."""
    query = GetUserQuery(user_id=id)
    result = await mediator.send(query)
    return UserResponse.model_validate(result)
```

### 3. Repository Pattern

**Interface (Domain Layer)**
```python
from abc import ABC, abstractmethod
from typing import Optional, List

class IUserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        pass
    
    @abstractmethod
    async def add(self, user: User) -> None:
        pass
    
    @abstractmethod
    async def list_all(self) -> List[User]:
        pass
```

**Implementation (Infrastructure Layer)**
```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

class UserRepository(IUserRepository):
    def __init__(self, db: AsyncSession):
        self._db = db
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self._db.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def add(self, user: User) -> None:
        db_user = UserModel(**user.to_dict())
        self._db.add(db_user)
        await self._db.flush()
```

### 4. Pydantic Models

**Request Model**
```python
from pydantic import BaseModel, Field, EmailStr, validator

class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    
    @field_validator('email')
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return v.lower()
```

**Response Model**
```python
from datetime import datetime

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    email: str
    created_at: datetime
    updated_at: Optional[datetime] = None
```

### 5. Dependency Injection

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db() -> AsyncSession:
    async with AsyncSession(engine) as session:
        yield session

def get_user_repository(
    db: AsyncSession = Depends(get_db)
) -> IUserRepository:
    return UserRepository(db)

def get_mediator(
    repository: IUserRepository = Depends(get_user_repository)
) -> Mediator:
    mediator = Mediator()
    mediator.register(CreateUserCommand, CreateUserCommandHandler(repository))
    mediator.register(GetUserQuery, GetUserQueryHandler(repository))
    return mediator
```

### 6. Exception Handling

**Custom Exception**
```python
class UserNotFoundException(Exception):
    def __init__(self, user_id: int):
        self.user_id = user_id
        super().__init__(f"User with ID {user_id} not found")
```

**Exception Handler**
```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(UserNotFoundException)
async def user_not_found_handler(
    request: Request,
    exc: UserNotFoundException
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "type": "/errors/user-not-found",
            "title": "User Not Found",
            "status": 404,
            "detail": str(exc),
            "instance": str(request.url)
        }
    )
```

### 7. HTTP Client

```python
from building_blocks.infrastructure.http import (
    HttpClient, HttpClientConfig, BearerAuth
)

# Configuration
config = HttpClientConfig(
    base_url="https://api.example.com",
    auth_strategy=BearerAuth(token="your-token"),
    timeout=30.0,
    enable_circuit_breaker=True
)

# Usage
async with HttpClient(config) as client:
    response = await client.get("/users")
    data = response.json()
```

### 8. Redis Caching

```python
from building_blocks.infrastructure.cache import RedisCache, RedisConfig

config = RedisConfig(
    host="localhost",
    port=6379,
    password=None,
    db=0
)

cache = RedisCache(config)
await cache.start()

# Set with TTL
await cache.set("user:1", json.dumps(user_data), ttl=300)

# Get
data = await cache.get("user:1")

# Delete
await cache.delete("user:1")
```

### 9. Event Publishing

**Define Event**
```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class UserCreatedEvent:
    user_id: int
    email: str
    name: str
    occurred_at: datetime
```

**Publish Event**
```python
event = UserCreatedEvent(
    user_id=user.id,
    email=user.email,
    name=user.name,
    occurred_at=datetime.utcnow()
)
await event_publisher.publish(event)
```

### 10. Logging

**Structured Logging**
```python
import logging

logger = logging.getLogger(__name__)

logger.info(
    "User created successfully",
    extra={
        "user_id": user.id,
        "email": user.email,  # Auto-redacted if sensitive
        "correlation_id": correlation_id,
        "trace_id": trace_id
    }
)

logger.error(
    "Failed to create user",
    extra={"error": str(exc), "correlation_id": correlation_id},
    exc_info=True
)
```

## 🗂️ Project Structure

```
src/building_blocks/
├── api/                    # Exception handlers, responses
├── application/            # Mediator, commands, queries
├── domain/                 # Entities, events, repositories (interfaces)
├── infrastructure/         # DB, cache, HTTP, messaging
│   ├── cache/             # Redis implementation
│   ├── database/          # SQLAlchemy setup
│   ├── http/              # HTTP client
│   └── messaging/         # Kafka implementation
└── observability/         # Logging, tracing, metrics
```

## 🔍 Common Imports

```python
# FastAPI
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse

# Pydantic
from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator

# SQLAlchemy
from sqlalchemy import select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base

# Building Blocks
from building_blocks.application.mediator import Mediator, IRequestHandler
from building_blocks.domain.entities import Entity
from building_blocks.infrastructure.cache import RedisCache, RedisConfig
from building_blocks.infrastructure.http import HttpClient, HttpClientConfig

# Standard Library
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod
```

## 🎯 Type Hints Cheatsheet

```python
# Basic types
def func(name: str, age: int, active: bool) -> None:
    pass

# Optional (nullable)
def get_user(id: int) -> Optional[User]:
    pass

# Lists and Dicts
def process(items: List[str]) -> Dict[str, Any]:
    pass

# Union types (multiple possible types)
def handle(value: Union[int, str]) -> bool:
    pass
# Or with Python 3.10+
def handle(value: int | str) -> bool:
    pass

# Async functions
async def fetch_data(url: str) -> dict:
    pass

# Callable
from typing import Callable
def execute(func: Callable[[int], str]) -> None:
    pass
```

## 📊 Database Operations

```python
# Select
result = await session.execute(select(User).where(User.id == 1))
user = result.scalar_one_or_none()

# Insert
new_user = User(name="John", email="john@example.com")
session.add(new_user)
await session.commit()

# Update
await session.execute(
    update(User).where(User.id == 1).values(name="Jane")
)
await session.commit()

# Delete
await session.execute(delete(User).where(User.id == 1))
await session.commit()

# Bulk operations
users = [User(name=f"User {i}") for i in range(100)]
session.add_all(users)
await session.commit()
```

## 🔐 Environment Variables

```bash
# .env file
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db
REDIS_URL=redis://localhost:6379/0
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Optional
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
SECRET_KEY=your-secret-key
```

## 📱 HTTP Status Codes

```python
from fastapi import status

# Success
status.HTTP_200_OK              # GET, PUT, PATCH
status.HTTP_201_CREATED         # POST
status.HTTP_204_NO_CONTENT      # DELETE

# Client Errors
status.HTTP_400_BAD_REQUEST     # Validation error
status.HTTP_401_UNAUTHORIZED    # Not authenticated
status.HTTP_403_FORBIDDEN       # Not authorized
status.HTTP_404_NOT_FOUND       # Resource not found
status.HTTP_409_CONFLICT        # Duplicate resource

# Server Errors
status.HTTP_500_INTERNAL_SERVER_ERROR
status.HTTP_503_SERVICE_UNAVAILABLE
```

## 🧪 Testing Patterns

```python
# Pytest async test
@pytest.mark.asyncio
async def test_create_user():
    result = await create_user(...)
    assert result.name == "John"

# Mock dependency
@pytest.fixture
def mock_repository():
    return AsyncMock(spec=IUserRepository)

# Integration test with database
@pytest.fixture
async def db_session():
    async with AsyncSession(test_engine) as session:
        yield session
        await session.rollback()
```

## 🔗 Useful URLs (when service running)

- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health: http://localhost:8000/health
- Metrics: http://localhost:8000/metrics
- RedisInsight: http://localhost:5540
- pgAdmin: http://localhost:5050
- Grafana: http://localhost:3000

---

**See also:**
- [Full Documentation Index](INDEX.md)
- [AI Coding Rules](../.cursorrules)
- [Contributing Guide](CONTRIBUTING.md)
