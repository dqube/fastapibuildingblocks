# FastAPI Building Blocks

Reusable building blocks for FastAPI applications following Domain-Driven Design (DDD) principles with built-in observability.

## Overview

This package provides a comprehensive set of base classes and utilities for building FastAPI applications with a clean, domain-driven architecture. It includes:

- **Domain-Driven Design** patterns and building blocks
- **CQRS** (Command Query Responsibility Segregation) pattern with mediator
- **OpenTelemetry** observability (tracing, logging, metrics)
- **Grafana Stack** integration (Tempo, Loki, Prometheus, Grafana)
- **Docker** support with production-ready configurations

## Features

✨ **Mediator Pattern** - Decoupled command/query handling  
🔭 **Distributed Tracing** - OpenTelemetry with Grafana Tempo  
📊 **Metrics Collection** - Prometheus metrics for all operations  
📝 **Structured Logging** - JSON logs with trace correlation (Loki)  
🎯 **Automatic Instrumentation** - Zero-config observability for mediator pattern  
🐳 **Docker Support** - Production-ready Docker configurations  
📮 **Kafka Integration** - Wolverine-style integration events for microservices  
🔄 **Event-Driven Architecture** - Domain events and integration events  
⚡ **Async/Await** - Full async support throughout
- **Commands**: Write operations (CQRS pattern)
- **Queries**: Read operations (CQRS pattern)
- **Handlers**: Command and query handlers
- **Application Services**: Use case coordinators
- **DTOs**: Data Transfer Objects

### 3. Observability Layer
Built-in monitoring and debugging layer:
- **Tracing**: Distributed tracing with OpenTelemetry and Tempo
- **Logging**: Structured logging with trace correlation (Loki)
- **Metrics**: Prometheus metrics for HTTP and mediator operations
- **Middleware**: Automatic instrumentation for FastAPI
- **Configuration**: Flexible observability configuration

### 4. Domain Layer
The core business logic layer containing:
- **Entities**: Objects with identity and lifecycle
- **Value Objects**: Immutable objects defined by their attributes
- **Aggregates**: Clusters of entities and value objects
- **Domain Events**: Events representing business occurrences
- **Repositories**: Interfaces for data persistence
- **Domain Services**: Business logic that doesn't fit in entities
4. Infrastructure Layer
Technical implementation layer containing:
- **Persistence**: Database implementations
- **Repositories**: Repository implementations
- **Unit of Work**: Transaction management
- **Database**: Connection and session management
- **Messaging**: Event bus and message queue implementations
- **External Services**: Third-party integrations

### 5. Infrastructure Layer
Technical implementation layer containing:
- **Persistence**: Database implementations
- **Repositories**: Repository implementations
- **Unit of Work**: Transaction management
- **Database**: Connection and session management
- **Messaging**: Event bus and message queue implementations
- *Quick Start Options

### 1. Install the Package

```bash
make install
# or
pip install -e .
```

### 2. Run Example Service

```bash
# Local development
make run

# With Docker
make docker-deploy

# With full observability stack
make obs-all
```Make Commands

Similar to .NET CLI commands:

```bash
# Development
make install          # Install dependencies (like dotnet restore)
make run             # Run the service (like dotnet run)
make restart         # Restart the service
make build           # Build the package (like dotnet build)
make test            # Run tests (like dotnet test)

# Docker
make docker-build    # Build Docker image
make docker-deploy   # Deploy to Docker
make docker-stop     # Stop Docker container

# Observability
make obs-up          # Start observability stack
make obs-down        # Stop observability stack
make run-with-obs    # Run with observability
make obs-all         # Start everything

# Code Quality
make format          # Format code
make lint            # Lint code
make clean           # Clean artifacts
```

## Documentation

- [MEDIATOR_PATTERN.md](MEDIATOR_PATTERN.md) - Mediator pattern implementation
- [KAFKA_INTEGRATION.md](KAFKA_INTEGRATION.md) - Kafka integration events (Wolverine-style)
- [KAFKA_QUICKSTART.md](KAFKA_QUICKSTART.md) - 5-minute Kafka quick start guide
- [INBOX_OUTBOX_PATTERN.md](INBOX_OUTBOX_PATTERN.md) - Reliable messaging patterns
- [INBOX_OUTBOX_CONFIG.md](INBOX_OUTBOX_CONFIG.md) - Configuration guide for inbox/outbox
- [OBSERVABILITY.md](OBSERVABILITY.md) - Complete observability guide
- [DOCKER_GUIDE.md](DOCKER_GUIDE.md) - Docker deployment guide

## Usage (Basic)

### 3. Access the Services

- **API**: http://localhost:8000/docs
│   ├── mediator/       # Mediator pattern implementation
│   ├── commands/       # Command definitions
│   ├── queries/        # Query definitions
│   └── handlers/       # Command/Query handlers
├── observability/       # OpenTelemetry instrumentation
│   ├── tracing.py      # Distributed tracing (Tempo)
│   ├── logging.py      # Structured logging (Loki)
│   ├── metrics.py      # Metrics collection (Prometheus)
│   ├── middleware.py   # FastAPI middleware
│   └── config.py       # Configuration
├── infrastructure/      # Technical implementations
└── api/                # HTTP interface utilities
```

## Example Service

A complete example service is included in `example_service/` demonstrating:

- ✅ Mediator pattern with CQRS
- ✅ Repository pattern (in-memory implementation)
- ✅ Domain events
- ✅ RESTful API with FastAPI
- ✅ Full observability integration
- ✅ Docker deployment
- ✅ Health checks

Run it with:
```bash
cd example_service
make run
```

## Key Features Explained

### Automatic Mediator Instrumentation

Every `mediator.send()` call is automatically traced:

```python
# This single line creates:
# - A distributed trace span
# - Structured logs with correlation
# - Metrics (duration, success/failure)
result = await mediator.send(CreateUserCommand(email="user@example.com"))
```

### Trace Correlation

All telemetry is correlated:
- Logs include trace_id and span_id
- Metrics include exemplars (sample traces)
- Grafana links traces → logs → metrics automatically

### Zero-Config Observability

Just enable observability and everything is instrumented:
```python
setup_observability(app, ObservabilityConfig(service_name="my-service"))
# That's it! All HTTP requests and mediator calls are now traced
## Observability

Complete observability stack included:

```bash
# Start observability stack (Tempo, Loki, Prometheus, Grafana)
make obs-up

# Run application with observability
make run-with-obs

# View observability stack
make obs-status

# Access Grafana dashboard
open http://localhost:3000
```

See [OBSERVABILITY.md](OBSERVABILITY.md) for detailed documentation.

## Kafka Integration Events

Event-driven microservices communication with Kafka, similar to Wolverine's integration events in .NET:

```bash
# Start Kafka
docker-compose -f docker-compose.kafka.yml up -d

# Install dependencies
pip install -e ".[messaging]"

# Run example
python example_kafka_integration.py
```

Features:
- ✅ **Integration Events** - Cross-service communication via Kafka
- ✅ **Automatic Publishing** - Events published after command/query processing
- ✅ **Event Mapping** - Domain events → Integration events
- ✅ **Reliable Consumption** - Manual offset commit with retry logic
- ✅ **Dead Letter Queue** - Failed messages sent to DLQ
- ✅ **Full Observability** - Distributed tracing for all Kafka operations
- ✅ **Transactional Outbox** - Reliable publishing with database transactions
- ✅ **Idempotent Inbox** - Exactly-once message processing
- ✅ **Configurable Patterns** - Enable/disable inbox and outbox via configuration

### Configurable Inbox/Outbox Pattern

Control reliability patterns via configuration:

```python
from fastapi_building_blocks.infrastructure.messaging import (
    KafkaConfig,
    create_event_publisher,
)

# Option 1: Direct publishing (development)
config = KafkaConfig(
    enable_outbox=False,  # ❌ No database dependency
    enable_inbox=False,   # ❌ No duplicate detection
)

# Option 2: Full reliability (production - recommended!)
config = KafkaConfig(
    enable_outbox=True,   # ✅ Transactional outbox
    enable_inbox=True,    # ✅ Exactly-once processing
)

# Or via environment variables
# export KAFKA_ENABLE_OUTBOX=true
# export KAFKA_ENABLE_INBOX=true
config = KafkaConfig()

# Factory automatically chooses the right publisher
publisher = create_event_publisher(config, session=session)
await publisher.publish(event)
```

**When to enable:**
- `enable_outbox=True`: Production, when events must not be lost
- `enable_inbox=True`: Production, when duplicate processing is unacceptable  
- Both `False`: Development/testing only

See [INBOX_OUTBOX_CONFIG.md](INBOX_OUTBOX_CONFIG.md) for configuration guide and [INBOX_OUTBOX_PATTERN.md](INBOX_OUTBOX_PATTERN.md) for pattern details.

### Quick Example

```python
from fastapi_building_blocks.domain.events import IntegrationEvent
from fastapi_building_blocks.infrastructure.messaging import (
    create_event_publisher,
    create_integration_event_mediator,
)

# Define integration event
class UserCreatedIntegrationEvent(IntegrationEvent):
    user_id: UUID
    email: str

# Wrap mediator for automatic publishing
mediator = create_integration_event_mediator(
    base_mediator,
    publisher,
    mapper
)

# Send command - integration event published automatically!
await mediator.send(CreateUserCommand(...))
```

See [KAFKA_INTEGRATION.md](KAFKA_INTEGRATION.md) for complete documentation or [KAFKA_QUICKSTART.md](KAFKA_QUICKSTART.md) for a 5-minute quick start.

## Usage Examples

### Mediator Pattern

```python
from fastapi import FastAPI, Depends
from fastapi_building_blocks.application.mediator import Mediator, Command, Query
from fastapi_building_blocks.api.dependencies import MediatorDep

# Define a command
class CreateUserCommand(Command):
    email: str
    name: str

# Define a handler
class CreateUserHandler:
    async def handle(self, command: CreateUserCommand):
        # Your business logic
        return User(email=command.email, name=command.name)

# Use in FastAPI endpoint
@app.post("/users")
async def create_user(
    command: CreateUserCommand,
    mediator: MediatorDep  # Automatic dependency injection
):
    result = await mediator.send(command)
    return result
```

### Observability

```python
from fastapi import FastAPI
from fastapi_building_blocks.observability import (
    setup_observability,
    ObservabilityConfig,
)

app = FastAPI()

# Configure observability
config = ObservabilityConfig(
    service_name="my-service",
    tracing_enabled=True,
    logging_enabled=True,
    metrics_enabled=True,
)

# Setup (adds tracing, logging, metrics)
setup_observability(app, config)

# All requests and mediator.send() calls are now automatically instrumented!
```

## *External Services**: Third-party integrations

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
