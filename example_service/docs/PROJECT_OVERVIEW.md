# FastAPI User Management Service - Project Overview

## 🎯 Project Description

A production-ready FastAPI microservice demonstrating **Domain-Driven Design (DDD)** architecture using the `fastapi-building-blocks` package. This service provides complete user management functionality with proper separation of concerns across architectural layers.

## 🏗️ Architecture

This project follows **Clean Architecture** principles with **Domain-Driven Design**:

```
┌─────────────────────────────────────────────────────────┐
│                     API Layer (HTTP)                     │
│              FastAPI Routes & Dependencies               │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                  Application Layer                       │
│         Commands, Queries, Handlers (CQRS)              │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    Domain Layer                          │
│    Entities, Aggregates, Value Objects, Events          │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│               Infrastructure Layer                       │
│        Repositories, Database, External Services         │
└─────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
example_service/
├── app/
│   ├── domain/                    # Domain Layer (Business Logic)
│   │   ├── models/
│   │   │   └── user.py           # User aggregate with Email & UserProfile value objects
│   │   ├── events/
│   │   │   └── user_events.py    # Domain events (UserCreated, UserUpdated, etc.)
│   │   └── repositories/
│   │       └── user_repository.py # IUserRepository interface
│   │
│   ├── application/               # Application Layer (Use Cases)
│   │   ├── commands/
│   │   │   └── user_commands.py  # Write operations (Create, Update, Delete)
│   │   ├── queries/
│   │   │   └── user_queries.py   # Read operations (GetById, GetAll)
│   │   ├── handlers/
│   │   │   ├── user_command_handlers.py  # Command handlers
│   │   │   └── user_query_handlers.py    # Query handlers
│   │   └── dtos.py               # Data Transfer Objects
│   │
│   ├── infrastructure/            # Infrastructure Layer (Implementation)
│   │   └── repositories/
│   │       └── user_repository.py # InMemoryUserRepository implementation
│   │
│   ├── api/                       # API Layer (HTTP Interface)
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   └── users.py      # User REST endpoints
│   │   │   └── api.py            # API router
│   │   └── dependencies.py        # FastAPI dependency injection
│   │
│   ├── core/                      # Core Configuration
│   │   └── config.py             # Application settings
│   │
│   └── main.py                    # Application entry point
│
├── tests/
│   └── test_users_api.py         # API tests
├── requirements.txt               # Python dependencies
├── .env                          # Environment variables
├── start.sh                      # Quick start script
└── README.md
```

## 🔑 Key Design Patterns

### 1. **Domain-Driven Design (DDD)**
- **Aggregate Root**: `User` - maintains consistency boundaries
- **Value Objects**: `Email`, `UserProfile` - immutable domain concepts
- **Domain Events**: `UserCreatedEvent`, `UserUpdatedEvent`, `UserDeletedEvent`
- **Repository Pattern**: Abstract data access

### 2. **CQRS (Command Query Responsibility Segregation)**
- **Commands**: Write operations (CreateUser, UpdateUser, DeleteUser)
- **Queries**: Read operations (GetUserById, GetAllUsers)
- **Handlers**: Separate handlers for commands and queries

### 3. **Dependency Injection**
- FastAPI's native DI system
- Repository and handler dependencies
- Loose coupling between layers

### 4. **Clean Architecture**
- **Domain Layer**: Pure business logic, no dependencies
- **Application Layer**: Use cases, depends only on domain
- **Infrastructure Layer**: Technical implementations
- **API Layer**: HTTP interface, depends on application layer

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- Virtual environment activated

### Installation

```bash
# Navigate to example service
cd example_service

# Install dependencies
pip install -r requirements.txt
```

### Running the Service

**Option 1: Using the start script**
```bash
./start.sh
```

**Option 2: Manual start**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Option 3: Using Python**
```bash
python -m app.main
```

### Access the API

- **API Base**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📡 API Endpoints

### User Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/users/` | Create a new user |
| GET | `/api/v1/users/` | List all users (with pagination) |
| GET | `/api/v1/users/{user_id}` | Get user by ID |
| PUT | `/api/v1/users/{user_id}` | Update user |
| DELETE | `/api/v1/users/{user_id}` | Delete user (soft delete) |

### Example Requests

**Create User:**
```bash
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "bio": "Software engineer"
  }'
```

**Get All Users:**
```bash
curl "http://localhost:8000/api/v1/users/?skip=0&limit=10"
```

**Get User by ID:**
```bash
curl "http://localhost:8000/api/v1/users/{user_id}"
```

**Update User:**
```bash
curl -X PUT "http://localhost:8000/api/v1/users/{user_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "last_name": "Smith"
  }'
```

**Delete User:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/users/{user_id}"
```

## 🧪 Running Tests

```bash
pytest tests/ -v
```

## 🔧 Configuration

Edit `.env` file to configure:

```env
APP_NAME=User Management Service
APP_VERSION=1.0.0
DEBUG=True
API_V1_PREFIX=/api/v1
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
```

## 📚 Building Blocks Used

This service leverages the following building blocks:

### Domain Layer
- `BaseEntity` - Base class for entities with ID and timestamps
- `AggregateRoot` - Base for aggregates with domain events
- `ValueObject` - Immutable value objects
- `DomainEvent` - Base for domain events
- `IRepository` - Repository interface

### Application Layer
- `Command` / `CommandHandler` - CQRS write operations
- `Query` / `QueryHandler` - CQRS read operations
- `DTO` - Data transfer objects

### Infrastructure Layer
- `BaseRepository` - In-memory repository implementation
- `IUnitOfWork` - Transaction management interface

### API Layer
- `SuccessResponse` / `ErrorResponse` - Standardized responses
- `APIException` - Custom exceptions
- `NotFoundException`, `ConflictException`, etc.

## 🎓 Learning Points

### Domain Layer
1. **User Aggregate**: Encapsulates user business logic
2. **Value Objects**: Email and UserProfile ensure data integrity
3. **Domain Events**: Enable event-driven architecture
4. **Business Rules**: Encapsulated in domain methods (activate, deactivate, etc.)

### Application Layer
1. **CQRS Pattern**: Clear separation of reads and writes
2. **Handlers**: Single responsibility for each operation
3. **DTOs**: Decouple API from domain models

### Infrastructure Layer
1. **Repository Pattern**: Abstract data access
2. **In-Memory Storage**: Simple implementation for demo
3. **Index Management**: Email lookup optimization

### API Layer
1. **Dependency Injection**: Clean dependencies
2. **Standardized Responses**: Consistent API responses
3. **Error Handling**: Proper HTTP status codes and messages

## 🔄 Extending the Service

### Add a New Entity

1. **Domain Layer**: Create entity, events, repository interface
2. **Application Layer**: Create commands, queries, handlers, DTOs
3. **Infrastructure Layer**: Implement repository
4. **API Layer**: Create endpoints and dependencies

### Add Database Support

Replace `InMemoryUserRepository` with a database implementation:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from building_blocks.infrastructure import BaseRepository

class SQLAlchemyUserRepository(BaseRepository[User], IUserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_email(self, email: str) -> Optional[User]:
        # Database query implementation
        pass
```

### Add Event Bus

Publish domain events to an event bus:

```python
from building_blocks.infrastructure import IEventPublisher

class UserEventPublisher(IEventPublisher):
    async def publish(self, event: DomainEvent) -> None:
        # Publish to RabbitMQ, Redis, etc.
        pass
```

## 📖 Best Practices Demonstrated

1. ✅ **Separation of Concerns**: Each layer has clear responsibilities
2. ✅ **Dependency Inversion**: High-level modules don't depend on low-level modules
3. ✅ **Single Responsibility**: Each class has one reason to change
4. ✅ **Open/Closed**: Open for extension, closed for modification
5. ✅ **Type Safety**: Full type hints throughout
6. ✅ **Testability**: Easy to test each layer independently
7. ✅ **Event-Driven**: Domain events for side effects
8. ✅ **API Documentation**: Auto-generated with FastAPI
9. ✅ **Error Handling**: Proper exceptions and responses
10. ✅ **Configuration Management**: Environment-based settings

## 🤝 Contributing

This is an example project. Feel free to:
- Add more features (authentication, authorization, etc.)
- Implement database persistence
- Add more comprehensive tests
- Implement event sourcing
- Add CQRS with separate read models

## 📝 License

MIT License - Free to use and modify
