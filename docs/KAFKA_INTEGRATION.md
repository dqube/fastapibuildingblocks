# Kafka Integration Events

This document describes the Kafka integration event implementation, which provides cross-service communication similar to Wolverine's integration events in .NET.

## Overview

Integration events enable loosely coupled communication between microservices through message brokers. Unlike domain events (which are internal to a service), integration events cross bounded context boundaries.

### Key Features

- **Asynchronous Publishing**: Non-blocking event publishing to Kafka topics
- **Automatic Event Mapping**: Convert domain events to integration events
- **Reliable Consumption**: Manual offset commit with retry logic
- **Dead Letter Queue**: Failed messages are sent to DLQ for analysis
- **OpenTelemetry Integration**: Full distributed tracing and metrics
- **Type-Safe**: Strongly typed events with Pydantic validation
- **Mediator Integration**: Automatic publishing after command/query processing

## Architecture

```
Command/Query → Handler → Domain Events → Event Mapper → Integration Events → Kafka Producer → Kafka Topic
                                                                                                      ↓
Consumer → Integration Events → Event Handlers ← Kafka Consumer ← Kafka Topic
```

## Quick Start

### 1. Installation

Add the messaging optional dependency:

```bash
pip install fastapi-building-blocks[messaging]
```

Or install directly:

```bash
pip install aiokafka pydantic-settings
```

### 2. Define Integration Events

```python
from building_blocks.domain.events import IntegrationEvent
from uuid import UUID
from datetime import datetime

class UserCreatedIntegrationEvent(IntegrationEvent):
    """Published when a new user is created."""
    user_id: UUID
    email: str
    full_name: str
    created_at: datetime
```

### 3. Configure Kafka

Set environment variables:

```bash
export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
export KAFKA_SERVICE_NAME=user-service
export KAFKA_CONSUMER_GROUP_ID=user-service-group
```

Or configure programmatically:

```python
from building_blocks.infrastructure.messaging import KafkaConfig

config = KafkaConfig(
    bootstrap_servers="localhost:9092",
    service_name="user-service",
    consumer_group_id="user-service-group",
)
```

### 4. Publishing Events

#### Manual Publishing

```python
from building_blocks.infrastructure.messaging import (
    KafkaIntegrationEventPublisher,
    KafkaConfig,
)

# Create publisher
config = KafkaConfig()
publisher = KafkaIntegrationEventPublisher(config)

# Start publisher
await publisher.start()

try:
    # Publish event
    event = UserCreatedIntegrationEvent(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        created_at=datetime.utcnow(),
    )
    await publisher.publish(event)
finally:
    await publisher.stop()
```

#### Using Context Manager

```python
async with KafkaIntegrationEventPublisher(config) as publisher:
    await publisher.publish(event)
```

#### Batch Publishing

```python
events = [event1, event2, event3]
await publisher.publish_many(events)
```

### 5. Consuming Events

#### Define Event Handler

```python
from building_blocks.infrastructure.messaging import IntegrationEventHandler
from building_blocks.domain.events import IntegrationEvent

class UserCreatedHandler(IntegrationEventHandler):
    """Handles UserCreatedIntegrationEvent."""
    
    async def handle(self, event: UserCreatedIntegrationEvent) -> None:
        print(f"User created: {event.email}")
        # Your business logic here
        # - Send welcome email
        # - Update analytics
        # - Sync to CRM
        # etc.
```

#### Register Handler and Start Consumer

```python
from building_blocks.infrastructure.messaging import (
    KafkaIntegrationEventConsumer,
    KafkaConfig,
)

# Create consumer
config = KafkaConfig()
consumer = KafkaIntegrationEventConsumer(config)

# Register handlers
consumer.register_handler(
    UserCreatedIntegrationEvent,
    UserCreatedHandler()
)

# Start consuming
topics = ["integration-events.user_created"]
await consumer.start(topics)

# Consumer runs in background
# Call consumer.stop() to stop gracefully
```

#### Using Handler Functions

```python
async def handle_user_created(event: UserCreatedIntegrationEvent):
    print(f"User created: {event.email}")

consumer.register_handler_function(
    UserCreatedIntegrationEvent,
    handle_user_created
)
```

## Integration with Mediator (Wolverine-Style)

The most powerful feature is automatic integration event publishing through the mediator, similar to Wolverine's approach.

### 1. Map Domain Events to Integration Events

```python
from building_blocks.infrastructure.messaging import EventMapper

mapper = EventMapper()

# Simple 1-to-1 mapping
mapper.register_mapping(
    UserCreatedDomainEvent,
    UserCreatedIntegrationEvent
)

# Custom transformation
def transform_user_updated(domain_event: UserUpdatedDomainEvent) -> dict:
    return {
        "user_id": domain_event.aggregate_id,
        "email": domain_event.new_email,
        "updated_fields": domain_event.changed_fields,
    }

mapper.register_mapping(
    UserUpdatedDomainEvent,
    UserUpdatedIntegrationEvent,
    transform=transform_user_updated
)
```

### 2. Wrap Mediator with Integration Event Publishing

```python
from building_blocks.application.mediator import Mediator
from building_blocks.infrastructure.messaging import (
    create_integration_event_mediator,
)

# Create base mediator
base_mediator = Mediator()

# Wrap with integration event publishing
mediator = create_integration_event_mediator(
    base_mediator,
    publisher,
    mapper
)

# Now when you send commands, integration events are automatically published
result = await mediator.send(CreateUserCommand(...))
# Integration events are published automatically after successful execution!
```

### 3. Return Events from Handlers

Your command/query handlers can return events:

```python
from dataclasses import dataclass
from typing import List

@dataclass
class CreateUserResult:
    user_id: UUID
    domain_events: List[DomainEvent]
    integration_events: List[IntegrationEvent]  # Optional

class CreateUserHandler(RequestHandler[CreateUserCommand, CreateUserResult]):
    async def handle(self, command: CreateUserCommand) -> CreateUserResult:
        # Create user
        user = User.create(command.email, command.full_name)
        
        # Save to database
        await self.repository.save(user)
        
        # Return result with events
        return CreateUserResult(
            user_id=user.id,
            domain_events=user.domain_events,  # Will be auto-mapped
            # Or explicitly add integration events:
            integration_events=[
                UserCreatedIntegrationEvent(
                    user_id=user.id,
                    email=user.email,
                    full_name=user.full_name,
                )
            ]
        )
```

## Advanced Configuration

### Security (SASL/SSL)

```python
config = KafkaConfig(
    bootstrap_servers="broker1:9092,broker2:9092",
    security_protocol="SASL_SSL",
    sasl_mechanism="SCRAM-SHA-256",
    sasl_username="your-username",
    sasl_password="your-password",
    ssl_cafile="/path/to/ca-cert",
)
```

### Producer Settings

```python
config = KafkaConfig(
    # Performance tuning
    producer_batch_size=32768,  # 32KB
    producer_linger_ms=50,  # Wait up to 50ms to batch
    producer_compression_type="zstd",  # Best compression
    
    # Reliability
    producer_acks="all",  # Wait for all replicas
    producer_retries=5,
    enable_idempotence=True,  # Exactly-once semantics
)
```

### Consumer Settings

```python
config = KafkaConfig(
    consumer_group_id="my-service-group",
    consumer_auto_offset_reset="earliest",  # Read from beginning
    consumer_enable_auto_commit=False,  # Manual commit for reliability
    consumer_max_poll_records=1000,
    consumer_session_timeout_ms=60000,  # 60 seconds
)
```

### Dead Letter Queue

```python
config = KafkaConfig(
    enable_dlq=True,
    dlq_topic_suffix=".dlq",
    max_retry_attempts=3,
)
```

## Topic Naming

By default, topics follow the pattern: `integration-events.{event_name_in_snake_case}`

Customize topic naming:

```python
class UserCreatedIntegrationEvent(IntegrationEvent):
    def get_topic_name(self) -> str:
        return "users.created.v1"
```

## Partitioning Strategy

By default, events are partitioned by `aggregate_id` for ordering guarantees.

Customize partitioning:

```python
class UserCreatedIntegrationEvent(IntegrationEvent):
    def get_partition_key(self) -> str:
        # Partition by tenant for multi-tenancy
        return self.tenant_id
```

## FastAPI Integration

### Application Lifespan

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    publisher = KafkaIntegrationEventPublisher(config)
    await publisher.start()
    
    consumer = KafkaIntegrationEventConsumer(config)
    # Register handlers...
    await consumer.start(topics)
    
    app.state.publisher = publisher
    app.state.consumer = consumer
    
    yield
    
    # Shutdown
    await publisher.stop()
    await consumer.stop()

app = FastAPI(lifespan=lifespan)
```

### Dependency Injection

```python
from fastapi import Depends
from typing import Annotated

def get_event_publisher(request: Request) -> KafkaIntegrationEventPublisher:
    return request.app.state.publisher

PublisherDep = Annotated[KafkaIntegrationEventPublisher, Depends(get_event_publisher)]

@app.post("/users")
async def create_user(
    data: CreateUserRequest,
    publisher: PublisherDep,
):
    # Use publisher...
    await publisher.publish(event)
```

## Observability

All Kafka operations are automatically instrumented with OpenTelemetry:

- **Traces**: Spans for publish/consume operations with context propagation
- **Logs**: Structured logs for all events
- **Metrics**: Message counts, latencies, errors

View traces in Grafana Tempo and metrics in Prometheus.

## Error Handling

### Producer Errors

```python
from aiokafka.errors import KafkaError

try:
    await publisher.publish(event)
except KafkaError as e:
    logger.error(f"Failed to publish event: {e}")
    # Event is sent to DLQ if configured
```

### Consumer Errors

The consumer automatically retries failed messages up to `max_retry_attempts`. After max retries, messages are sent to the DLQ.

```python
class MyHandler(IntegrationEventHandler):
    async def handle(self, event: IntegrationEvent) -> None:
        try:
            # Process event
            pass
        except Exception as e:
            # Log error - consumer will retry
            logger.error(f"Handler error: {e}")
            raise  # Re-raise to trigger retry
```

## Best Practices

1. **Event Versioning**: Include `event_version` field and handle schema evolution
2. **Idempotency**: Handlers should be idempotent (safe to process multiple times)
3. **Correlation IDs**: Use correlation_id to track related events across services
4. **Small Events**: Keep event payloads small; store large data in database
5. **Event Sourcing**: Consider using events as source of truth
6. **Schema Registry**: Use a schema registry (like Confluent Schema Registry) for production
7. **Monitoring**: Monitor DLQ topics for failed messages
8. **Testing**: Mock events for unit tests, use embedded Kafka for integration tests

## Comparison with Wolverine

| Feature | Wolverine (.NET) | This Implementation |
|---------|------------------|---------------------|
| Integration Events | ✅ | ✅ |
| Auto Publishing | ✅ | ✅ (via mediator wrapper) |
| Message Bus Abstraction | ✅ | ✅ |
| Kafka Support | ✅ | ✅ |
| Type Safety | ✅ | ✅ (Pydantic) |
| Distributed Tracing | ✅ | ✅ (OpenTelemetry) |
| Dead Letter Queue | ✅ | ✅ |
| Retry Logic | ✅ | ✅ |
| Event Mapping | ✅ | ✅ |
| Saga Support | ✅ | ⚠️ (not yet implemented) |

## Examples

See the `example_service/` directory for a complete working example with:
- User service with integration events
- Email service consuming events
- Docker Compose setup with Kafka
- Observability stack integration

## Troubleshooting

### Connection Issues

```
Failed to start Kafka producer: KafkaConnectionError
```

Check:
- Kafka broker is running: `docker ps | grep kafka`
- Correct bootstrap servers in configuration
- Network connectivity to Kafka broker

### Consumer Not Receiving Messages

Check:
- Consumer is subscribed to correct topics
- Messages are being published to correct topics (check Kafka logs)
- Consumer group has not exceeded max members
- No consumer lag: `kafka-consumer-groups --describe --group my-group`

### Events Not Publishing Automatically

Check:
- Using wrapped mediator (not base mediator)
- Handler returns result with `domain_events` or `integration_events`
- Event mapping is registered
- Publisher is started

## References

- [Wolverine Documentation](https://wolverine.netlify.app/)
- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [aiokafka Documentation](https://aiokafka.readthedocs.io/)
- [Domain Events vs Integration Events](https://www.kamilgrzybek.com/design/domain-events-vs-integration-events/)
