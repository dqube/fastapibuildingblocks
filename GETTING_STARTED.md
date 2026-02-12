# FastAPI Building Blocks with DDD Example Service

Complete implementation of reusable FastAPI building blocks following Domain-Driven Design principles, plus a fully functional example service demonstrating their usage.

## 📦 What's Included

### 1. **fastapi-building-blocks** Package
A reusable Python package providing base classes and utilities for building FastAPI applications with clean DDD architecture.

**Location**: `src/fastapi_building_blocks/`

**Layers**:
- **Domain**: Entities, Value Objects, Aggregates, Domain Events, Repository Interfaces
- **Application**: Commands, Queries, Handlers, DTOs, Application Services
- **Infrastructure**: Repository Implementations, Unit of Work, Database Session, Messaging
- **API**: Dependencies, Middleware, Responses, Exceptions

### 2. **User Management Service** (Example)
A complete FastAPI microservice demonstrating how to use the building blocks package.

**Location**: `example_service/`

**Features**:
- Full CRUD operations for user management
- CQRS pattern implementation
- Domain events
- Clean architecture with proper layer separation
- API documentation with Swagger/ReDoc
- Comprehensive tests

## 🚀 Quick Start

### Step 1: Setup Environment

```bash
# Navigate to project root
cd /Users/mdevendran/python/fastapibuildingblocks

# Activate virtual environment (already exists with Python 3.14)
source .venv/bin/activate

# Install building blocks package
pip install -e .
```

### Step 2: Run the Example Service

```bash
# Navigate to example service
cd example_service

# Install service dependencies
pip install -r requirements.txt

# Start the service
./start.sh
```

Or manually:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 3: Test the API

**Option 1: Using the test script**
```bash
# In a new terminal (while service is running)
python test_api.py
```

**Option 2: Using Swagger UI**
Visit: http://localhost:8000/docs

**Option 3: Using curl**
```bash
# Create a user
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "bio": "Test bio"
  }'

# Get all users
curl "http://localhost:8000/api/v1/users/"
```

## 📚 Documentation

- **Building Blocks Package**: See `README.md` in project root
- **Example Service**: See `example_service/PROJECT_OVERVIEW.md`
- **API Documentation**: http://localhost:8000/docs (when running)

## 🏗️ Project Structure

```
fastapibuildingblocks/
├── src/fastapi_building_blocks/     # Building blocks package
│   ├── domain/                       # Domain layer base classes
│   ├── application/                  # Application layer base classes
│   ├── infrastructure/               # Infrastructure layer base classes
│   └── api/                         # API layer utilities
│
├── example_service/                  # Example FastAPI service
│   ├── app/
│   │   ├── domain/                  # User domain model
│   │   ├── application/             # Commands, queries, handlers
│   │   ├── infrastructure/          # Repository implementation
│   │   ├── api/                     # REST endpoints
│   │   ├── core/                    # Configuration
│   │   └── main.py                  # App entry point
│   ├── tests/                       # Test files
│   ├── requirements.txt
│   ├── start.sh                     # Start script
│   └── test_api.py                  # API test script
│
├── tests/                           # Building blocks tests
├── pyproject.toml                   # Package configuration
├── .env                            # Environment variables
└── README.md                       # This file
```

## 🎯 Key Features

### Building Blocks Package

✅ **Domain Layer**
- `BaseEntity` - Base class for entities with identity
- `ValueObject` - Immutable value objects
- `AggregateRoot` - Aggregates with domain events
- `DomainEvent` - Base for domain events
- `IRepository` - Repository interface
- `DomainService` - Base for domain services

✅ **Application Layer**
- `Command` / `CommandHandler` - CQRS write operations
- `Query` / `QueryHandler` - CQRS read operations
- `Handler` - Generic message handler
- `ApplicationService` - Application service base
- `DTO` - Data transfer objects

✅ **Infrastructure Layer**
- `BaseRepository` - In-memory repository implementation
- `IUnitOfWork` - Transaction management
- `DatabaseSession` - Database connection management
- `IMessageBus` / `IEventPublisher` - Event handling
- `ExternalService` - Third-party integration base

✅ **API Layer**
- `Dependency` - FastAPI dependency base
- `BaseMiddleware` - Middleware base class
- `SuccessResponse` / `ErrorResponse` - Standardized responses
- Custom exceptions with proper HTTP status codes

### Example Service Features

✅ **Complete User Management**
- Create, Read, Update, Delete users
- Pagination support
- Active/inactive user filtering

✅ **DDD Implementation**
- User aggregate with Email and UserProfile value objects
- Domain events (UserCreated, UserUpdated, UserDeleted)
- Repository pattern with in-memory implementation

✅ **CQRS Pattern**
- Separate commands and queries
- Dedicated handlers for each operation

✅ **Clean Architecture**
- Proper layer separation
- Dependency injection
- Testable components

## 🧪 Running Tests

### Building Blocks Tests
```bash
pytest tests/ -v
```

### Example Service Tests
```bash
cd example_service
pytest tests/ -v
```

### API Integration Tests
```bash
# Start the service first
cd example_service
./start.sh

# In another terminal
python test_api.py
```

## 📖 Usage Examples

### Using Building Blocks in Your Project

1. **Install the package**:
```bash
pip install fastapi-building-blocks
```

2. **Create your domain model**:
```python
from fastapi_building_blocks.domain import AggregateRoot, ValueObject

class Email(ValueObject):
    value: str

class User(AggregateRoot):
    email: Email
    name: str
```

3. **Create commands and handlers**:
```python
from fastapi_building_blocks.application import Command, CommandHandler

class CreateUserCommand(Command):
    email: str
    name: str

class CreateUserHandler(CommandHandler):
    async def handle(self, command: CreateUserCommand):
        # Implementation
        pass
```

4. **Create API endpoints**:
```python
from fastapi import APIRouter
from fastapi_building_blocks.api.responses import SuccessResponse

router = APIRouter()

@router.post("/users")
async def create_user(command: CreateUserCommand):
    result = await handler.handle(command)
    return SuccessResponse.create(data=result)
```

## 🔧 Configuration

### Building Blocks Package
Configure in `pyproject.toml`

### Example Service
Configure in `example_service/.env`:
```env
APP_NAME=User Management Service
APP_VERSION=1.0.0
DEBUG=True
API_V1_PREFIX=/api/v1
CORS_ORIGINS=["http://localhost:3000"]
```

## 🚢 Deploying Your Service

The example service can be deployed to any platform that supports Python/FastAPI:

- **Docker**: Create a Dockerfile
- **Cloud**: AWS Lambda, Google Cloud Run, Azure Functions
- **PaaS**: Heroku, Railway, Render
- **Kubernetes**: Deploy with standard manifests

## 📈 Next Steps

### Enhance the Building Blocks
1. Add database implementations (SQLAlchemy, MongoDB)
2. Implement event bus (RabbitMQ, Redis)
3. Add authentication/authorization utilities
4. Create caching decorators
5. Add observability (logging, metrics, tracing)

### Extend the Example Service
1. Add authentication (JWT, OAuth2)
2. Implement database persistence
3. Add event sourcing
4. Create separate read models (CQRS)
5. Add background tasks
6. Implement rate limiting
7. Add comprehensive monitoring

## 🤝 Contributing

Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests
- Improve documentation
- Share your projects using these building blocks

## 📝 License

MIT License - Free to use and modify for any purpose

## 🙏 Acknowledgments

Built with:
- **FastAPI** - Modern, fast web framework
- **Pydantic** - Data validation using Python type annotations
- **Uvicorn** - Lightning-fast ASGI server

Inspired by:
- Domain-Driven Design by Eric Evans
- Clean Architecture by Robert C. Martin
- CQRS and Event Sourcing patterns

## 📞 Support

For questions or issues:
1. Check the documentation in `PROJECT_OVERVIEW.md`
2. Review the example service code
3. Visit http://localhost:8000/docs for API documentation
4. Run the test script to see working examples

---

**Happy Coding! 🚀**

Built with ❤️ using FastAPI and Domain-Driven Design principles.
