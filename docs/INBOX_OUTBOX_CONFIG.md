# Inbox/Outbox Configuration Guide

## Quick Reference

### Configuration Options

| Setting | Default | Description | When to Enable |
|---------|---------|-------------|----------------|
| `enable_outbox` | `False` | Store events in database before publishing | ✅ Production, when data consistency is critical |
| `enable_inbox` | `False` | Store message IDs to detect duplicates | ✅ Production, when exactly-once processing is required |

### Configuration Methods

#### 1. Environment Variables (Recommended)

```bash
# Enable outbox pattern
export KAFKA_ENABLE_OUTBOX=true

# Enable inbox pattern
export KAFKA_ENABLE_INBOX=true

# Both enabled (full reliability)
export KAFKA_ENABLE_OUTBOX=true
export KAFKA_ENABLE_INBOX=true
```

Then in code:
```python
config = KafkaConfig()  # Loads from environment
```

#### 2. Direct Configuration

```python
from building_blocks.infrastructure.messaging import KafkaConfig

config = KafkaConfig(
    enable_outbox=True,
    enable_inbox=True,
)
```

#### 3. .env File

```env
# .env file
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_ENABLE_OUTBOX=true
KAFKA_ENABLE_INBOX=true
KAFKA_SERVICE_NAME=my-service
```

With python-dotenv:
```python
from dotenv import load_dotenv
load_dotenv()

config = KafkaConfig()  # Automatically loads from .env
```

## Configuration Scenarios

### Scenario 1: Development/Testing
**Need:** Fast iteration, no persistence overhead

```python
config = KafkaConfig(
    enable_outbox=False,  # ❌ Direct publishing
    enable_inbox=False,   # ❌ No duplicate detection
)
```

**Characteristics:**
- ⚡ Lowest latency
- 💾 No database tables needed
- ⚠️ Events can be lost
- ⚠️ Duplicates possible

### Scenario 2: Staging/Pre-Production
**Need:** Test reliability patterns

```python
config = KafkaConfig(
    enable_outbox=True,   # ✅ Transactional outbox
    enable_inbox=True,    # ✅ Duplicate detection
)
```

**Characteristics:**
- 🔒 Full reliability
- 💾 Requires database tables
- ⏱️ Slightly higher latency
- ✅ Production-ready

### Scenario 3: Production (Recommended)
**Need:** Maximum reliability and consistency

```bash
# Environment variables
export KAFKA_ENABLE_OUTBOX=true
export KAFKA_ENABLE_INBOX=true
```

```python
config = KafkaConfig()  # Loads from environment
```

**Characteristics:**
- ✅ No event loss
- ✅ Exactly-once processing
- ✅ Transactional consistency
- ✅ Audit trail

### Scenario 4: Hybrid (Publisher Only)
**Need:** Reliable publishing, simple consuming

```python
config = KafkaConfig(
    enable_outbox=True,   # ✅ Reliable publishing
    enable_inbox=False,   # ❌ Simple consuming
)
```

**Use when:**
- Publishing is critical
- Consumer can tolerate duplicates
- Lower consumer overhead preferred

### Scenario 5: Hybrid (Consumer Only)
**Need:** Simple publishing, reliable consuming

```python
config = KafkaConfig(
    enable_outbox=False,  # ❌ Direct publishing
    enable_inbox=True,    # ✅ Duplicate detection
)
```

**Use when:**
- Consuming is critical
- Publisher has simple requirements
- Events are not critical on producer side

## Database Requirements

### When Outbox is Enabled

**Required:**
```sql
-- Outbox table (automatically created)
CREATE TABLE outbox_messages (
    id UUID PRIMARY KEY,
    event_id UUID NOT NULL,
    event_type VARCHAR(255) NOT NULL,
    topic VARCHAR(255) NOT NULL,
    payload TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL,
    -- ... more columns
);
```

**Background Worker:**
```python
# Outbox relay must be started
relay = OutboxRelay(config, session_factory)
await relay.start()
```

### When Inbox is Enabled

**Required:**
```sql
-- Inbox table (automatically created)
CREATE TABLE inbox_messages (
    message_id UUID PRIMARY KEY,
    event_type VARCHAR(255) NOT NULL,
    topic VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'processing',
    received_at TIMESTAMP NOT NULL,
    -- ... more columns
);
```

## Publisher Usage

### With Factory (Recommended)

The factory automatically chooses the right publisher:

```python
from building_blocks.infrastructure.messaging import create_event_publisher

# Auto-selects outbox or direct based on config
publisher = create_event_publisher(
    kafka_config=config,
    session=session if config.enable_outbox else None
)

await publisher.publish(event)
```

### Direct Publisher Selection

```python
if config.enable_outbox:
    # Requires session
    from building_blocks.infrastructure.messaging import OutboxEventPublisher
    from building_blocks.infrastructure.persistence.outbox import OutboxRepository
    
    repository = OutboxRepository(session)
    publisher = OutboxEventPublisher(repository, "my-service")
else:
    # No session required
    from building_blocks.infrastructure.messaging import KafkaIntegrationEventPublisher
    
    publisher = KafkaIntegrationEventPublisher(config, "my-service")
```

## Consumer Usage

### With Inbox Pattern

```python
from building_blocks.infrastructure.messaging import InboxIntegrationEventConsumer

consumer = InboxIntegrationEventConsumer(
    kafka_config=config,
    session_factory=session_factory,
    enable_inbox=None,  # None = use config.enable_inbox
)

# If enable_inbox=True: Uses database for duplicate detection
# If enable_inbox=False: Direct processing, no database
```

## Complete FastAPI Example

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from building_blocks.infrastructure.messaging import (
    KafkaConfig,
    create_event_publisher,
    OutboxRelay,
)
from building_blocks.infrastructure.persistence.outbox import CREATE_OUTBOX_TABLE_SQL
from building_blocks.infrastructure.persistence.inbox import CREATE_INBOX_TABLE_SQL

# Load configuration from environment
def get_config():
    return KafkaConfig()

async def init_database(config: KafkaConfig):
    """Initialize database tables based on configuration."""
    async with get_session() as session:
        if config.enable_outbox:
            await session.execute(CREATE_OUTBOX_TABLE_SQL)
            print("✅ Outbox table created")
        
        if config.enable_inbox:
            await session.execute(CREATE_INBOX_TABLE_SQL)
            print("✅ Inbox table created")
        
        await session.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    config = get_config()
    
    # Initialize database
    await init_database(config)
    
    # Start outbox relay if enabled
    relay = None
    if config.enable_outbox:
        relay = OutboxRelay(config, get_session_factory())
        await relay.start()
        print(f"✅ Outbox relay started (poll interval: {relay.poll_interval_seconds}s)")
    
    yield
    
    if relay:
        await relay.stop()
        print("✅ Outbox relay stopped")

app = FastAPI(lifespan=lifespan)

# Dependency that provides the right publisher
async def get_publisher(
    session: AsyncSession = Depends(get_session),
    config: KafkaConfig = Depends(get_config),
):
    return create_event_publisher(
        kafka_config=config,
        session=session if config.enable_outbox else None,
    )

@app.post("/users")
async def create_user(
    email: str,
    full_name: str,
    session: AsyncSession = Depends(get_session),
    publisher = Depends(get_publisher),
):
    """
    Create user endpoint.
    
    Automatically uses outbox or direct publishing based on
    KAFKA_ENABLE_OUTBOX environment variable.
    """
    async with session.begin():
        # Save user
        user_id = str(uuid4())
        # ... save to database
        
        # Publish event
        event = UserCreatedIntegrationEvent(
            user_id=user_id,
            email=email,
            full_name=full_name,
        )
        await publisher.publish(event)
    
    return {"user_id": user_id}
```

## Troubleshooting

### Outbox Not Working

**Symptom:** Events stored in outbox but not published

**Check:**
1. ✅ Is outbox relay running?
2. ✅ Is Kafka connection working?
3. ✅ Check relay logs for errors
4. ✅ Verify `status='pending'` in outbox_messages table

```python
# Check pending messages
SELECT * FROM outbox_messages WHERE status = 'pending';
```

### Inbox Duplicates

**Symptom:** Messages processed multiple times

**Check:**
1. ✅ Is `enable_inbox=True`?
2. ✅ Is inbox table created?
3. ✅ Check inbox_messages for duplicates

```python
# Check inbox
SELECT message_id, status, attempt_count 
FROM inbox_messages 
WHERE event_type = 'UserCreatedIntegrationEvent';
```

### Configuration Not Loading

**Symptom:** Settings not applied

**Check:**
1. ✅ Environment variables have `KAFKA_` prefix
2. ✅ python-dotenv loaded (if using .env)
3. ✅ Print config to verify

```python
config = KafkaConfig()
print(f"Outbox enabled: {config.enable_outbox}")
print(f"Inbox enabled: {config.enable_inbox}")
```

## Performance Impact

| Configuration | Latency | Throughput | Database Load | Reliability |
|--------------|---------|------------|---------------|-------------|
| Both disabled | Lowest | Highest | None | Lowest |
| Outbox only | Medium | Medium | Medium (writes) | High (publish) |
| Inbox only | Medium | Medium | Medium (writes+reads) | High (consume) |
| Both enabled | Highest | Lower | High (writes+reads) | Highest |

**Recommendation:** Use both patterns in production despite the overhead—reliability is more important than raw performance.

## See Also

- [INBOX_OUTBOX_PATTERN.md](INBOX_OUTBOX_PATTERN.md) - Detailed pattern documentation
- [example_configurable_inbox_outbox.py](example_configurable_inbox_outbox.py) - Working examples
- [KAFKA_INTEGRATION.md](KAFKA_INTEGRATION.md) - General Kafka integration guide
