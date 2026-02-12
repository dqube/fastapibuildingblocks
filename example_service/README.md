# User Management Service

A FastAPI microservice demonstrating Domain-Driven Design (DDD) architecture using the `fastapi-building-blocks` package.

## Project Structure

```
example_service/
├── app/
│   ├── domain/              # Domain layer - business logic
│   │   ├── models/          # Domain entities and aggregates
│   │   ├── events/          # Domain events
│   │   └── repositories/    # Repository interfaces
│   ├── application/         # Application layer - use cases
│   │   ├── commands/        # Write operations (CQRS)
│   │   ├── queries/         # Read operations (CQRS)
│   │   └── handlers/        # Command and query handlers
│   ├── infrastructure/      # Infrastructure layer - implementations
│   │   ├── repositories/    # Repository implementations
│   │   └── persistence/     # Database configuration
│   ├── api/                 # API layer - HTTP interface
│   │   ├── v1/             # API version 1
│   │   │   └── endpoints/  # API endpoints
│   │   ├── dependencies.py  # FastAPI dependencies
│   │   └── middleware.py    # Custom middleware
│   ├── core/               # Core configuration
│   │   ├── config.py       # Application settings
│   │   └── container.py    # Dependency injection container
│   └── main.py             # Application entry point
├── tests/                   # Test files
├── .env                     # Environment variables
└── requirements.txt         # Project dependencies
```

## Features

- **User Management**: Create, read, update, delete users
- **DDD Architecture**: Clear separation of concerns across layers
- **CQRS Pattern**: Separate read and write operations
- **Repository Pattern**: Abstract data access
- **Event-Driven**: Domain events for side effects
- **Dependency Injection**: Clean dependencies with FastAPI

## Installation

```bash
pip install -r requirements.txt
```

## Running the Service

**Option 1: Using the start script**
```bash
./start.sh
```

**Option 2: Direct command with full Python path**
```bash
/Users/mdevendran/python/fastapibuildingblocks/.venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Option 3: With activated virtual environment**
```bash
# From project root
cd /Users/mdevendran/python/fastapibuildingblocks
source .venv/bin/activate
cd example_service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Example API Endpoints

- `POST /api/v1/users` - Create a new user
- `GET /api/v1/users/{user_id}` - Get user by ID
- `GET /api/v1/users` - List all users
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user
