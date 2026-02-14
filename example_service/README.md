# User Management Service

A production-ready FastAPI microservice demonstrating Domain-Driven Design (DDD) architecture, event-driven patterns, and enterprise messaging using the `fastapi-building-blocks` package.

## Features

### Core Architecture
- **Domain-Driven Design (DDD)**: Clear separation of concerns across domain, application, infrastructure, and API layers
- **CQRS Pattern**: Separate command and query operations for optimal read/write performance
- **Mediator Pattern**: Decoupled request handling with built-in instrumentation
- **Repository Pattern**: Abstract data access with clean interfaces
- **Dependency Injection**: Clean dependencies with FastAPI's DI system

### User Management
- ✅ Create, read, update, and delete users
- ✅ Query users by ID, email, or retrieve all users
- ✅ Validation and error handling
- ✅ RESTful API design

### Event-Driven Messaging
- ✅ **Kafka Integration**: Asynchronous message publishing and consuming
- ✅ **Outbox Pattern**: Transactional reliability - messages saved to database before Kafka publish
- ✅ **Inbox Pattern**: Exactly-once message processing with duplicate detection
- ✅ **Outbox Relay Worker**: Background worker publishes pending outbox messages every 5 seconds
- ✅ **Integration Events**: Cross-service communication with typed events
- ✅ **Message Storage**: Persistent message history in PostgreSQL

### Observability
- ✅ **OpenTelemetry**: Distributed tracing, logging, and metrics
- ✅ **Structured Logging**: JSON-formatted logs with correlation IDs
- ✅ **Request/Response Logging**: Automatic HTTP request/response capture
- ✅ **Sensitive Data Redaction**: PII protection in logs
- ✅ **Metrics Endpoint**: Prometheus-compatible metrics at `/metrics`

### Database & Infrastructure
- ✅ **PostgreSQL**: Async database access with SQLAlchemy
- ✅ **pgAdmin**: Web-based database management UI
- ✅ **Multiple Tables**: users, messages, inbox_messages, outbox_messages
- ✅ **Connection Pooling**: Optimized database connections
- ✅ **Docker Compose**: Complete infrastructure orchestration

## Project Structure

```
example_service/
├── app/
│   ├── domain/                    # Domain layer - business logic
│   │   ├── entities/             # Domain entities and value objects
│   │   │   ├── user.py           # User entity
│   │   │   └── message.py        # Message entity
│   │   ├── events/               # Domain events
│   │   │   └── message_events.py # MessageSentIntegrationEvent
│   │   └── repositories/         # Repository interfaces
│   │       └── user_repository.py
│   ├── application/              # Application layer - use cases
│   │   ├── commands/             # Write operations (CQRS)
│   │   │   ├── user_commands.py  # CreateUser, UpdateUser, DeleteUser
│   │   │   └── message_commands.py # SendMessage
│   │   ├── queries/              # Read operations (CQRS)
│   │   │   ├── user_queries.py   # GetUserById, GetAllUsers
│   │   │   └── message_queries.py # GetMessages, GetMessagesBySender
│   │   ├── handlers/             # Command and query handlers
│   │   │   ├── user_command_handlers.py
│   │   │   ├── user_query_handlers.py
│   │   │   ├── message_command_handlers.py
│   │   │   ├── message_query_handlers.py
│   │   │   └── message_integration_handlers.py # Kafka consumer handler
│   │   └── dtos/                 # Data transfer objects
│   ├── infrastructure/           # Infrastructure layer
│   │   ├── repositories/         # Repository implementations
│   │   │   └── postgres_user_repository.py
│   │   └── persistence/
│   │       └── repositories/
│   │           └── message_repository.py
│   ├── api/                      # API layer - HTTP interface
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── users.py      # User CRUD endpoints
│   │   │   │   └── messages.py   # Message endpoints
│   │   │   └── api.py
│   │   └── dependencies.py       # FastAPI dependencies
│   ├── core/                     # Core configuration
│   │   ├── config.py             # Application settings
│   │   └── database.py           # Database session factory
│   └── main.py                   # Application entry point (lifespan events)
├── docker-compose.yml            # Infrastructure orchestration
├── init.sql                      # Database schema initialization
├── pgadmin_servers.json          # pgAdmin configuration
├── requirements.txt              # Python dependencies
└── Dockerfile                    # Container image definition
```

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Make (optional, for convenience commands)

### Running with Docker Compose (Recommended)

1. **Start all services**:
```bash
docker-compose up -d
```

This starts:
- **API Service** (port 8000)
- **PostgreSQL** (port 5432)
- **pgAdmin** (port 5050)
- **Kafka** (port 9092)
- **Zookeeper** (port 2181)

2. **View logs**:
```bash
docker-compose logs -f api
```

3. **Stop services**:
```bash
docker-compose down
```

### Accessing Services

- **API Documentation**: http://localhost:8000/docs
- **API (Swagger UI)**: http://localhost:8000/docs
- **API (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics
- **pgAdmin**: http://localhost:5050
  - Email: `admin@admin.com`
  - Password: `admin`
  - Server: `postgres` (already configured)

### Using Make Commands

```bash
# Start services
make up

# Stop services
make down

# View logs
make logs

# Rebuild services
make build

# Access database shell
make db-shell

# Run tests
make test
```

## API Endpoints

### User Management
- `POST /api/v1/users` - Create a new user
- `GET /api/v1/users/{user_id}` - Get user by ID
- `GET /api/v1/users/email/{email}` - Get user by email
- `GET /api/v1/users/` - List all users (with pagination)
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user

### Message Management
- `POST /api/v1/messages/send` - Send message to Kafka (via outbox)
- `GET /api/v1/messages/` - Get all messages
- `GET /api/v1/messages/sender/{sender}` - Get messages by sender
- `GET /api/v1/messages/{message_id}` - Get message by ID

### System
- `GET /health` - Health check endpoint
- `GET /metrics` - Prometheus metrics
- `GET /` - Service information

## Example Usage

### Create a User
```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true
  }'
```

### Send a Message to Kafka
```bash
curl -X POST http://localhost:8000/api/v1/messages/send \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hello from FastAPI!",
    "sender": "john@example.com",
    "metadata": {
      "category": "notification",
      "priority": "high"
    }
  }'
```

### Retrieve Messages
```bash
# Get all messages
curl http://localhost:8000/api/v1/messages/

# Get messages by sender
curl http://localhost:8000/api/v1/messages/sender/john@example.com
```

## Inbox/Outbox Pattern Flow

### Outbox Pattern (Publishing)
1. API receives message send request
2. Handler saves message to `outbox_messages` table with status='pending'
3. Transaction commits (atomic with business data)
4. **OutboxRelay worker** polls database every 5 seconds
5. Worker publishes pending messages to Kafka
6. Updates status='published' with timestamp

**Benefits**: Transactional consistency, no lost messages, automatic retries

### Inbox Pattern (Consuming)
1. Consumer receives message from Kafka
2. Checks `inbox_messages` table for duplicate (by message_id)
3. If duplicate, skips processing (idempotence)
4. If new, inserts to inbox with status='processing'
5. Processes message (saves to `messages` table)
6. Updates inbox status='processed'
7. Commits transaction and Kafka offset

**Benefits**: Exactly-once processing, duplicate detection, transactional safety

## Database Schema

### Tables
- `users` - User accounts
- `messages` - Processed messages from Kafka
- `outbox_messages` - Pending/published events (outbox pattern)
- `inbox_messages` - Received messages for deduplication (inbox pattern)

### Inspecting the Database

**Using pgAdmin** (http://localhost:5050):
1. Login with admin@admin.com / admin
2. Server "postgres" is pre-configured
3. Navigate to: Servers → postgres → Databases → user_management → Schemas → public → Tables

**Using psql**:
```bash
# Access database shell
docker exec -it postgres-db psql -U postgres -d user_management

# List tables
\dt

# Query outbox messages
SELECT event_id, event_type, status, created_at, published_at 
FROM outbox_messages 
ORDER BY created_at DESC 
LIMIT 10;

# Query inbox messages
SELECT message_id, event_type, status, received_at, processed_at 
FROM inbox_messages 
ORDER BY received_at DESC 
LIMIT 10;

# Query processed messages
SELECT message_id, sender, content, timestamp, processed_at 
FROM messages 
ORDER BY timestamp DESC 
LIMIT 10;
```

## Configuration

Environment variables can be set in `.env` or via Docker Compose:

### Application Settings
- `APP_NAME` - Service name (default: "User Management Service")
- `DEBUG` - Debug mode (default: true)
- `DATABASE_URL` - PostgreSQL connection string

### Kafka Settings
- `KAFKA_BOOTSTRAP_SERVERS` - Kafka broker (default: kafka:9092)
- `KAFKA_CONSUMER_GROUP` - Consumer group ID
- `KAFKA_ENABLE_OUTBOX` - Enable outbox pattern (default: true)
- `KAFKA_ENABLE_INBOX` - Enable inbox pattern (default: true)

### Observability Settings
- `TRACING_ENABLED` - Enable distributed tracing (default: true)
- `LOGGING_ENABLED` - Enable structured logging (default: true)
- `METRICS_ENABLED` - Enable metrics collection (default: true)
- `LOG_LEVEL` - Logging level (default: INFO)
- `LOG_REDACTION_ENABLED` - Redact sensitive data (default: true)

## Architecture Patterns

### CQRS (Command Query Responsibility Segregation)
- **Commands**: Write operations that change state (CreateUser, SendMessage)
- **Queries**: Read operations that return data (GetUser, GetMessages)
- Separate models and handlers for optimal performance

### Mediator Pattern
- Central request dispatcher
- Handlers registered via dependency injection
- Built-in instrumentation and logging
- Decouples senders from receivers

### Repository Pattern
- Abstract data access behind interfaces
- Easy to swap implementations (SQL, NoSQL, cache)
- Testable with mock repositories

### Event-Driven Architecture
- Integration events for cross-service communication
- Asynchronous processing with Kafka
- Domain events for internal side effects

## Monitoring & Observability

### Structured Logging
All logs are JSON-formatted with:
- Timestamp
- Trace ID & Span ID (distributed tracing)
- Logger name
- Service context
- Custom fields

### Metrics
Prometheus-compatible metrics at `/metrics`:
- HTTP request duration
- Request count by endpoint
- Database connection pool stats
- Kafka consumer lag
- Custom business metrics

### Tracing
OpenTelemetry integration for distributed tracing:
- HTTP request spans
- Database query spans
- Kafka publish/consume spans
- Mediator operation spans

## Development

### Local Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
docker-compose up -d postgres
python -m alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests
```bash
# Unit tests
pytest tests/

# Integration tests
pytest tests/ -m integration

# With coverage
pytest --cov=app tests/
```

### Building Docker Image
```bash
docker build -t user-management-service .
```

## Troubleshooting

### Check Service Health
```bash
curl http://localhost:8000/health
```

### View Kafka Topics
```bash
docker exec -it kafka kafka-topics.sh --list --bootstrap-server localhost:9092
```

### View Kafka Messages
```bash
docker exec -it kafka kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic integration-events.message_sent \
  --from-beginning
```

### Reset Kafka Consumer Group
```bash
docker exec -it kafka kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --group user-management-api-group \
  --reset-offsets --to-earliest --execute \
  --topic integration-events.message_sent
```

## Technology Stack

- **FastAPI** - Modern async web framework
- **SQLAlchemy** - Async ORM
- **PostgreSQL** - Relational database
- **Apache Kafka** - Event streaming
- **OpenTelemetry** - Observability
- **Pydantic** - Data validation
- **Docker** - Containerization
- **pgAdmin** - Database management

## License

MIT License
