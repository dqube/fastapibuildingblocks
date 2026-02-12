# FastAPI Building Blocks

Reusable building blocks for FastAPI applications following Domain-Driven Design (DDD) principles.

## Overview

This package provides a comprehensive set of base classes and utilities for building FastAPI applications with a clean, domain-driven architecture. It's designed to be used as a foundation for all your FastAPI projects.

## Architecture Layers

### 1. Domain Layer
The core business logic layer containing:
- **Entities**: Objects with identity and lifecycle
- **Value Objects**: Immutable objects defined by their attributes
- **Aggregates**: Clusters of entities and value objects
- **Domain Events**: Events representing business occurrences
- **Repositories**: Interfaces for data persistence
- **Domain Services**: Business logic that doesn't fit in entities

### 2. Application Layer
The use case orchestration layer containing:
- **Commands**: Write operations (CQRS pattern)
- **Queries**: Read operations (CQRS pattern)
- **Handlers**: Command and query handlers
- **Application Services**: Use case coordinators
- **DTOs**: Data Transfer Objects

### 3. Infrastructure Layer
Technical implementation layer containing:
- **Persistence**: Database implementations
- **Repositories**: Repository implementations
- **Unit of Work**: Transaction management
- **Database**: Connection and session management
- **Messaging**: Event bus and message queue implementations
- **External Services**: Third-party integrations

### 4. API Layer
HTTP interface layer containing:
- **Dependencies**: FastAPI dependency injection utilities
- **Middleware**: HTTP middleware components
- **Responses**: Standardized response models
- **Exceptions**: Custom exception handlers

## Installation

```bash
pip install -e .
```

For development:
```bash
pip install -e ".[dev]"
```

With database support:
```bash
pip install -e ".[database]"
```

With messaging support:
```bash
pip install -e ".[messaging]"
```

## Usage

```python
from fastapi_building_blocks.domain.entities import BaseEntity
from fastapi_building_blocks.application.commands import Command
from fastapi_building_blocks.infrastructure.persistence.repositories import BaseRepository
from fastapi_building_blocks.api.responses import SuccessResponse

# Create your domain entities
class User(BaseEntity):
    name: str
    email: str

# Define commands
class CreateUserCommand(Command):
    name: str
    email: str

# Implement repositories
class UserRepository(BaseRepository[User]):
    pass

# Build your FastAPI application with these building blocks
```

## Project Structure

```
src/fastapi_building_blocks/
├── domain/              # Core business logic
├── application/         # Use cases and orchestration
├── infrastructure/      # Technical implementations
└── api/                # HTTP interface utilities
```

## Contributing

Contributions are welcome! Please follow the DDD principles when adding new building blocks.

## License

MIT
