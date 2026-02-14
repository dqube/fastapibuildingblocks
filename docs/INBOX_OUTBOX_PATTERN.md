# Inbox/Outbox Pattern for Reliable Messaging

This document describes the Inbox and Outbox pattern implementation for ensuring reliable, exactly-once message processing in distributed systems.

## Overview

The Inbox/Outbox pattern solves critical problems in event-driven microservices:

### Problems Solved

1. **Lost Events**: Service crashes before publishing events to Kafka
2. **Duplicate Processing**: Same message processed multiple times
3. **Data Inconsistency**: Business data saved but event not published (or vice versa)
4. **Audit Trail**: No record of what events were published/consumed

### Configuration

**The inbox and outbox patterns are now fully configurable!** You can enable or disable them independently:

```python
from building_blocks.infrastructure.messaging import KafkaConfig

# Option 1: Direct publishing (no outbox, no inbox)
config = KafkaConfig(
    enable_outbox=False,  # Publish directly to Kafka
    enable_inbox=False,   # No duplicate detection
)

# Option 2: Outbox only (reliable publishing)
config = KafkaConfig(
    enable_outbox=True,   # Store in database before publishing
    enable_inbox=False,   # Direct consuming
)

# Option 3: Inbox only (exactly-once consuming)
config = KafkaConfig(
    enable_outbox=False,  # Direct publishing
    enable_inbox=True,    # Detect duplicates via database
)

# Option 4: Both patterns (maximum reliability) - RECOMMENDED for production
config = KafkaConfig(
    enable_outbox=True,   # Transactional outbox
    enable_inbox=True,    # Idempotent inbox
)
```

### Environment Variables

You can also configure via environment variables:

```bash
# Enable outbox pattern
export KAFKA_ENABLE_OUTBOX=true

# Enable inbox pattern
export KAFKA_ENABLE_INBOX=true

# Bootstrap servers
export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

Then load configuration:

```python
config = KafkaConfig()  # Automatically loads from environment
```

### Patterns

#### Outbox Pattern (Publishing)
Store outgoing integration events in a database table before publishing to Kafka. A background worker reads from the outbox and publishes to Kafka.

**Benefits:**
- ✅ Atomic commits with business data (same transaction)
- ✅ No event loss even if service crashes
- ✅ Automatic retry for failed publishes
- ✅ Audit trail of all published events

#### Inbox Pattern (Consuming)
Store incoming message IDs in a database table to detect duplicates and ensure idempotent processing.

**Benefits:**
- ✅ Exactly-once processing semantics
- ✅ Duplicate detection
- ✅ Transactional message processing
- ✅ Audit trail of all consumed events

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       Producer Service                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  API Endpoint                                                   │
│      ↓                                                          │
│  Begin Transaction                                              │
│      ↓                                                          │
│  Save Business Data (users table)                               │
│      ↓                                                          │
│  Save Integration Event (outbox_messages table) ◄─ Same TX!    │
│      ↓                                                          │
│  Commit Transaction                                             │
│      ↓                                                          │
│  [Outbox Relay Worker polls every 5 seconds]                   │
│      ↓                                                          │
│  Read pending messages from outbox                              │
│      ↓                                                          │
│  Publish to Kafka                                               │
│      ↓                                                          │
│  Mark as published in outbox                                    │
│                                                                 │
└───────────────────────────┼─────────────────────────────────────┘
                            ↓
                       Kafka Topic
                            ↓
┌───────────────────────────┼─────────────────────────────────────┐
│                      Consumer Service                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Receive message from Kafka                                     │
│      ↓                                                          │
│  Begin Transaction                                              │
│      ↓                                                          │
│  Check inbox_messages for message_id (duplicate check)          │
│      ↓                                                          │
│  If duplicate → Skip processing                                 │
│      ↓                                                          │
│  If new → Insert into inbox (status=processing)                 │
│      ↓                                                          │
│  Process message (update business data)                         │
│      ↓                                                          │
│  Update inbox (status=processed)                                │
│      ↓                                                          │
│  Commit Transaction                                             │
│      ↓                                                          │
│  Commit Kafka offset                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Database Schema

### Outbox Table

```sql
CREATE TABLE outbox_messages (
    id UUID PRIMARY KEY,
    event_id UUID NOT NULL,
    event_type VARCHAR(255) NOT NULL,
    event_version VARCHAR(50) NOT NULL,
    topic VARCHAR(255) NOT NULL,
    partition_key VARCHAR(255),
    payload TEXT NOT NULL,
    headers TEXT,
    correlation_id UUID,
    causation_id UUID,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    published_at TIMESTAMP,
    locked_until TIMESTAMP,
    attempt_count INT NOT NULL DEFAULT 0,
    last_error TEXT,
    source_service VARCHAR(255),
    aggregate_id UUID
);

-- Indexes for performance
CREATE INDEX ix_outbox_status_created ON outbox_messages(status, created_at);
CREATE INDEX ix_outbox_pending_locked ON outbox_messages(status, locked_until);
```

### Inbox Table

```sql
CREATE TABLE inbox_messages (
    message_id UUID PRIMARY KEY,  -- Event ID from Kafka message
    event_type VARCHAR(255) NOT NULL,
    event_version VARCHAR(50) NOT NULL,
    topic VARCHAR(255) NOT NULL,
    partition VARCHAR(50) NOT NULL,
    offset VARCHAR(50) NOT NULL,
    correlation_id UUID,
    status VARCHAR(50) NOT NULL DEFAULT 'processing',
    received_at TIMESTAMP NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMP,
    locked_until TIMESTAMP,
    attempt_count INT NOT NULL DEFAULT 0,
    last_error TEXT,
    handler_name VARCHAR(255),
    payload TEXT  -- Optional: for debugging/replay
);

-- Indexes for performance
CREATE INDEX ix_inbox_status_received ON inbox_messages(status, received_at);
CREATE INDEX ix_inbox_topic_partition_offset ON inbox_messages(topic, partition, offset);
```

## Usage

### Quick Start with Factory

The easiest way to use the patterns is via the publisher factory:

```python
from building_blocks.infrastructure.messaging import (
    KafkaConfig,
    create_event_publisher,
)

# Configuration (enable/disable patterns as needed)
config = KafkaConfig(
    enable_outbox=True,  # ✅ Use outbox pattern
    e3. Alternative: Use Outbox Publisher Directly

If you want explicit control: Use inbox pattern
)

# Create publisher - automatically chooses outbox or direct based on config
async with get_session() as session:
    publisher = create_event_publisher(
        kafka_config=config,
        session=session,  # Required if enable_outbox=True, optional otherwise
    )
    
    # Publish event (will use outbox if enabled)
    await publisher.publish(my_event)
```

### Outbox Pattern (Publishing)

#### 1. Setup Database

```python
from building_blocks.infrastructure.persistence.outbox import (
    CREATE_OUTBOX_TABLE_SQL
)

# Run the SQL to create the table
await session.execute(CREATE_OUTBOX_TABLE_SQL)
```

#### 2. Use Outbox Publisher

```python
from building_blocks.infrastructure.messaging import OutboxEventPublisher
from building_blocks.infrastructure.persistence.outbox import OutboxRepository

# In your endpoint/handler
async def create_user(command: CreateUserCommand, session: Session):
    # Begin transaction
    async with session.begin():
        # 1. Save business data
        user = User.create(command.email, command.full_name)
        await user_repository.save(user)
        
        # 2. Save integration event to outbox (SAME TRANSACTION!)
        outbox_repository = OutboxRepository(session)
        publisher = OutboxEventPublisher(outbox_repository, "user-service")
        
        event = UserCreatedIntegrationEvent(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
        )
        await publisher.publish(event)
        
        # 3. Commit atomically
        # Both business data and outbox message are committed together
    
    return {"user_id": user.id}
```4. Start Outbox Relay Worker (Only if Outbox is Enabled)

#### 3. Start Outbox Relay Worker

```python
from building_blocks.infrastructure.messaging import OutboxRelay
from building_blocks.infrastructure.messaging import KafkaConfig

# Configure
config = KafkaConfig(
    bootstrap_servers="localhost:9092",
    service_name="user-service",
)

# Create relay
relay = OutboxRelay(
    kafka_config=config,
    session_factory=get_session_factory(),
    poll_interval_seconds=5,  # Poll every 5 seconds
    batch_size=100,  # Process up to 100 messages per batch
    max_attempts=3,  # Retry up to 3 times
)

# Start relay (runs in background)
await relay.start()

# Relay will continue running, publishing pending messages to Kafka
# Stop gracefully when shutting down
await relay.stop()
```

#### 4. FastAPI Integration

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asyconfig = KafkaConfig()
    
    # Only start relay if outbox is enabled
    relay = None
    if config.enable_outbox:
        relay = OutboxRelay(config, get_session_factory())
        await relay.start()
        app.state.outbox_relay = relay
        print("✅ Outbox relay enabled and started")
    else:
        print("ℹ️ Outbox disabled - using direct publishing")
    
    yield
    
    # Shutdown
    if relay:
        
    # Shutdown: Stop relay
    await relay.stop()

app = FastAPI(lifespan=lifespan)
```

### Inbox Pattern (Consuming)
Only create table if inbox is enabled
if config.enable_inbox:
    #### 1. Setup Database

```python
from building_blocks.infrastructure.persistence.inbox import (
    CREATE_INBOX_TABLE_SQL
)

# Run the SQL to create the table
await session.execute(CREATE_INBOX_TABLE_SQL)
```

#### 2. Define Handler

```python
from building_blocks.infrastructure.messaging import (
    InboxIntegrationEventHandler
)

class UserCreatedHandler(InboxIntegrationEventHandler):
    """Handle UserCreatedIntegrationEvent with inbox pattern."""
    
    async def handle(self, event: UserCreatedIntegrationEvent, session: Session) -> None:
        # Session is provided by the consumer
        # All operations in this handler are part of the same transaction
        # that includes the inbox insert
        
        # 1. Process the event
        print(f"User created: {event.email}")
        
        # 2. Update your database
        notification = WelcomeNotification(
            user_id=event.user_id,
            email=event.email,
            sent=False,
        )
        session.add(notification)
        
        # 3. No need to commit - consumer will commit after marking inbox as processed
        # This ensures atomicity: either both notification is saved AND inbox is marked processed,
        # or neither happens
```

#### 3. Start Inbox Consumer

```python
    enable_inbox=True,  # ✅ Enable inbox pattern
)

# Create consumer
# enable_inbox parameter can override config if needed
consumer = InboxIntegrationEventConsumer(
    kafka_config=config,
    session_factory=get_session_factory(),
    store_payload=True,  # Store payload for debugging
    enable_inbox=None,   # None = use config.enable_inbox, or True/False to override
)

# Register handlers
consumer.register_handler(
    UserCreatedIntegrationEvent,
    UserCreatedHandler()
)

# Start consuming
# If enable_inbox=True: Uses inbox pattern (stores in database)
# If enable_inbox=False: Direct processing (no database storage)
await consumer.start(["users.created"])

# Consumer runs in background
# Stop gracefully when shutting down
await consumer.stop()
```

**Note**: When `enable_inbox=False`, the consumer processes messages directly without storing them in the inbox table. This means:
- ✅ Lower overhead (no database writes)
- ❌ No duplicate detection
- ❌ No exactly-once guarantees
- ❌ No audit trail UserCreatedHandler()
)create_event_publisher,
    KafkaConfig,
)

# Configuration (from environment or code)
def get_config():
    return KafkaConfig(
        enable_outbox=True,  # Configurable!
    )

# Event definition
class UserCreatedIntegrationEvent(IntegrationEvent):
    user_id: str
    email: str
    full_name: str

# Database dependency
async def get_session() -> AsyncSession:
    async with session_factory() as session:
        yield session

# Publisher dependency (automatically uses outbox or direct based on config)
async def get_publisher(
    session: AsyncSession = Depends(get_session),
    config: KafkaConfig = Depends(get_config),
):
    return create_event_publisher(
        config,
        session=session if config.enable_outbox else None
    )

# Application lifespan (conditional outbox relay)
@asynccontextmanager
async def lifespan(app: FastAPI):
    config = get_config()
    
    # Start outbox relay only if enabled
    relay = None
    if config.enable_outbox:
        from building_blocks.infrastructure.messaging import OutboxRelay
        relay = OutboxRelay(config, session_factory)
        await relay.start()
    
    yield
    
    if relay:
        await relay.stop()

app = FastAPI(lifespan=lifespan)

# Endpoint
@app.post("/users")
async def create_user(
    data: CreateUserRequest,
    session: AsyncSession = Depends(get_session),
    publisher = Depends(get_publisher),
):
    async with session.begin():
        # Save user
        user = User(email=data.email, full_name=data.full_name)
        session.add(user)
        
        # Publish event (uses outbox if enabled, direct otherwise)
    
    yield
    
    await relay.stop()

app = FastAPI(lifespan=lifespan)

# Endpoint
@app.post("/users")
async def create_user(
    data: CreateUserRequest,
    session: AsyncSession = Depends(get_session),
    publisher: OutboxEventPublisher = Depends(get_outbox_publisher),
):
    async with session.begin():
        # Save user
        user = User(email=data.email, full_name=data.full_name)
        session.add(user)
        
        # Publish event to outbox
        event = UserCreatedIntegrationEvent(
            user_id=str(user.id),
            email=user.email,
            full_name=user.full_name,
        )
        await publisher.publish(event)
        
        # Commit atomically
    
    return {"user_id": str(user.id)}
```

### Consumer Service

```python
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from building_blocks.infrastructure.messaging import (
    InboxIntegrationEventConsumer,
    InboxIntegrationEventHandler,
    KafkaConfig,
)

# Event handler
class UserCreatedHandler(InboxIntegrationEventHandler):
    async def handle(self, event: UserCreatedIntegrationEvent, session: AsyncSession):
        # Send welcome email (example)
        notification = WelcomeNotification(
            user_id=event.user_id,
            email=event.email,
        )
        session.add(notification)
        # Transaction will be committed by consumer

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start inbox consumer
    config = KafkaConfig(consumer_group_id="email-service-group")
    consumer = InboxIntegrationEventConsumer(config, session_factory)
    consumer.register_handler(UserCreatedIntegrationEvent, UserCreatedHandler())
    await consumer.start(["users.created"])
    
    yield
    
    await consumer.stop()

app = FastAPI(lifespan=lifespan)
```

## Advanced Topics

### Cleanup Old Messages

```python
from building_blocks.infrastructure.persistence.outbox import OutboxRepository
from building_blocks.infrastructure.persistence.inbox import InboxRepository

async def cleanup_old_messages():
    async with session_factory() as session:
        # Clean up old outbox messages (older than 7 days)
        outbox_repo = OutboxRepository(session)
        deleted = await outbox_repo.cleanup_old_messages(days=7)
        print(f"Deleted {deleted} old outbox messages")
        
        # Clean up old inbox messages (older than 30 days)
        inbox_repo = InboxRepository(session)
        deleted = await inbox_repo.cleanup_old_messages(days=30)
        print(f"Deleted {deleted} old inbox messages")
        
        await session.commit()
```

### Monitor Failed Messages

```python
async def monitor_failed_messages():
    async with session_factory() as session:
        # Check outbox for failed messages
        outbox_repo = OutboxRepository(session)
        failed = await outbox_repo.get_failed_messages(limit=100)
        
        for message in failed:
            print(f"Failed outbox message: {message.event_type}")
            print(f"Error: {message.last_error}")
            print(f"Attempts: {message.attempt_count}")
        
        # Check inbox for failed messages
        inbox_repo = InboxRepository(session)
        failed = await inbox_repo.get_failed_messages(limit=100)
        
        for message in failed:
            print(f"Failed inbox message: {message.event_type}")
            print(f"Error: {message.last_error}")
```

### Retry Failed Messages

```python
async def retry_failed_message(message_id: UUID):
    async with session_factory() as session:
        outbox_repo = OutboxRepository(session)
        await outbox_repo.retry_failed_message(message_id)
        await session.commit()
```

### Handle Stuck Messages

```python
async def handle_stuck_inbox_messages():
    async with session_factory() as session:
        inbox_repo = InboxRepository(session)
        
        # Get messages stuck in processing (older than 30 minutes)
        stuck = await inbox_repo.get_stuck_messages(timeout_minutes=30)
        
        for message in stuck:
            print(f"Stuck message: {message.event_type}")
            # Could retry or mark as failed
            await inbox_repo.retry_failed_message(message.message_id)
        
        await session.commit()
```

## Monitoring

### Metrics to Track

**Outbox:**
- Pending message count
- Messages published per second
- Publish success/failure rate
- Average time in outbox
- Failed message count

**Inbox:**
- Messages processed per second
- Duplicate message count
- Processing success/failure rate
- Average processing time
- Failed message count

### Grafana Queries (Prometheus)

```promql
# Outbox pending messages
sum(outbox_pending_messages_total)

# Outbox publish rate
rate(outbox_published_messages_total[5m])

# Inbox duplicate rate
rate(inbox_duplicate_messages_total[5m]) / rate(inbox_received_messages_total[5m])

# Inbox processing latency
histogram_quantile(0.95, inbox_processing_duration_seconds_bucket)
```

## Best Practices

1. **Outbox Relay Configuration**
   - Poll interval: 5-10 seconds (balance between latency and load)
   - Batch size: 100-1000 (depending on message size)
   - Multiple workers: Use locking to prevent duplicate publishing

2. **Cleanup Strategy**
   - Outbox: Delete after 7-14 days (archive if needed)
   - Inbox: Delete after 30-90 days (keep longer for audit)
   - Run cleanup jobs daily during off-peak hours

3. **Error Handling**
   - Max attempts: 3-5 retries
   - Exponential backoff: Optional, can be implemented
**Set:** `enable_outbox=True`

### Use Inbox Pattern When:
- ✅ Exactly-once processing is required
- ✅ Duplicate messages are possible
- ✅ Need audit trail of consumed messages
- ✅ Production environment

**Set:** `enable_inbox=True`

### Use Direct Publishing When:
- ⚠️ Prototyping/development only
- ⚠️ Events are not critical
- ⚠️ No database transactions
- ⚠️ Willing to accept potential data loss
- ⚠️ Performance is critical over reliability

**Set:** `enable_outbox=False` and `enable_inbox=False`

**Recommendation**: Always use both patterns (`enable_outbox=True` and `enable_inbox=True`)

5. **Partitioning** (for very high volume)
   - Partition tables by created_at (monthly)
   - Archive old partitions
   - Keeps active table small

## Comparison: Direct vs. Outbox

| Aspect | Direct Publishing | Outbox Pattern |
|--------|------------------|----------------|
| Data Consistency | ❌ Can lose events | ✅ Atomic with data |
| Resilience | ❌ Lost on crash | ✅ Survives crashes |
| Latency | ✅ Lower (immediate) | ⚠️ Higher (relay delay) |
| Complexity | ✅ Simpler | ⚠️ More complex |
| Audit Trail | ❌ No record | ✅ Full history |
| Retry | ❌ Manual | ✅ Automatic |
| Production Ready | ❌ Not recommended | ✅ Recommended |

## When to Use

### Use Outbox Pattern When:
- ✅ Data consistency is critical
- ✅ Cannot afford to lose events
- ✅ Need audit t
- See [example_configurable_inbox_outbox.py](example_configurable_inbox_outbox.py) for complete examples of all configuration options
- See [KAFKA_INTEGRATION.md](KAFKA_INTEGRATION.md) for general Kafka integration guide  
- Set `KAFKA_ENABLE_OUTBOX=true` and `KAFKA_ENABLE_INBOX=true` in your environment for production
- ✅ Using database transactions
- ✅ Production environment

### Use Direct Publishing When:
- ⚠️ Prototyping/development only
- ⚠️ Events are not critical
- ⚠️ No database transactions
- ⚠️ Willing to accept potential data loss

**Recommendation**: Always use Outbox/Inbox pattern in production!

## Troubleshooting

### Outbox messages not being published

Check:
1. Outbox relay worker is running
2. Kafka connection is working
3. Messages are in 'pending' status
4. Messages are not locked indefinitely
5. Check relay logs for errors

### Duplicate message processing

Check:
1. Inbox pattern is enabled
2. message_id is being used correctly
3. Database transaction commits are working
4. No race conditions in consumer code

### Performance degradation

Check:
1. Database indexes are present
2. Cleanup jobs are running
3. Table sizes are reasonable
4. Query execution plans

## References

- [Transactional Outbox Pattern](https://microservices.io/patterns/data/transactional-outbox.html)
- [Inbox Pattern for Idempotency](https://www.softwaredesign.ing/blog/inbox-pattern)
- [Event-Driven Architecture Patterns](https://martinfowler.com/articles/201701-event-driven.html)

---

**Next Steps**: See [example_inbox_outbox.py](example_inbox_outbox.py) for a complete working example.
