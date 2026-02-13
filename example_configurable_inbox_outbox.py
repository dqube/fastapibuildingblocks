"""
Example: Configurable Inbox/Outbox Pattern

This example demonstrates how to enable/disable inbox and outbox patterns
using configuration. The patterns can be toggled via environment variables
or code, allowing you to choose between:

1. Direct publishing (no outbox, no database dependency)
2. Outbox pattern (transactional publishing with database)
3. Inbox pattern (exactly-once consuming with database)
4. Both patterns (full reliability)
"""

import asyncio
import os
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Depends
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker

from fastapi_building_blocks.domain.events.integration_event import IntegrationEvent
from fastapi_building_blocks.infrastructure.messaging import (
    KafkaConfig,
    create_event_publisher,
    IntegrationEventPublisherFactory,
    InboxIntegrationEventConsumer,
    InboxIntegrationEventHandler,
    OutboxRelay,
)
from fastapi_building_blocks.infrastructure.persistence.outbox import (
    OutboxMessage,
    CREATE_OUTBOX_TABLE_SQL,
)
from fastapi_building_blocks.infrastructure.persistence.inbox import (
    InboxMessage,
    CREATE_INBOX_TABLE_SQL,
)


# ============================================================================
# Event Definitions
# ============================================================================

class UserCreatedIntegrationEvent(IntegrationEvent):
    """User created integration event."""
    user_id: str
    email: str
    full_name: str


class WelcomeEmailSentIntegrationEvent(IntegrationEvent):
    """Welcome email sent integration event."""
    user_id: str
    email: str


# ============================================================================
# Configuration Examples
# ============================================================================

def get_config_direct():
    """Direct publishing - no database dependency."""
    return KafkaConfig(
        bootstrap_servers="localhost:9092",
        service_name="user-service",
        enable_outbox=False,  # ✅ Disabled - publish directly to Kafka
        enable_inbox=False,   # ✅ Disabled - no duplicate detection
    )


def get_config_outbox_only():
    """Outbox pattern for reliable publishing."""
    return KafkaConfig(
        bootstrap_servers="localhost:9092",
        service_name="user-service",
        enable_outbox=True,   # ✅ Enabled - store events in database
        enable_inbox=False,   # ❌ Disabled - consumer doesn't use inbox
    )


def get_config_inbox_only():
    """Inbox pattern for exactly-once consuming."""
    return KafkaConfig(
        bootstrap_servers="localhost:9092",
        service_name="email-service",
        consumer_group_id="email-service-group",
        enable_outbox=False,  # ❌ Disabled - publish directly
        enable_inbox=True,    # ✅ Enabled - detect duplicates
    )


def get_config_full_reliability():
    """Both patterns for maximum reliability."""
    return KafkaConfig(
        bootstrap_servers="localhost:9092",
        service_name="user-service",
        consumer_group_id="user-service-group",
        enable_outbox=True,   # ✅ Enabled - transactional outbox
        enable_inbox=True,    # ✅ Enabled - exactly-once processing
    )


def get_config_from_env():
    """Load configuration from environment variables."""
    # Set via environment:
    # export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
    # export KAFKA_ENABLE_OUTBOX="true"
    # export KAFKA_ENABLE_INBOX="true"
    return KafkaConfig()


# ============================================================================
# Database Setup
# ============================================================================

# Database connection
DATABASE_URL = "postgresql+asyncpg://user:password@localhost/mydb"

async_engine = create_async_engine(DATABASE_URL, echo=True)
async_session_factory = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_database(enable_outbox: bool, enable_inbox: bool):
    """Initialize database tables based on configuration."""
    async with async_engine.begin() as conn:
        if enable_outbox:
            await conn.execute(CREATE_OUTBOX_TABLE_SQL)
            print("✅ Created outbox_messages table")
        
        if enable_inbox:
            await conn.execute(CREATE_INBOX_TABLE_SQL)
            print("✅ Created inbox_messages table")


async def get_session() -> AsyncSession:
    """Get database session."""
    async with async_session_factory() as session:
        yield session


# ============================================================================
# Example 1: Direct Publishing (No Outbox)
# ============================================================================

async def example_direct_publishing():
    """
    Direct publishing without outbox pattern.
    
    Pros:
    - Simple, no database dependency
    - Lower latency
    
    Cons:
    - Events can be lost if service crashes before publishing
    - No transactional consistency with business data
    """
    print("\n" + "="*80)
    print("Example 1: Direct Publishing (No Outbox)")
    print("="*80)
    
    config = get_config_direct()
    
    # Create publisher (no session needed)
    publisher = create_event_publisher(config)
    
    async with publisher:
        event = UserCreatedIntegrationEvent(
            user_id=str(uuid4()),
            email="john@example.com",
            full_name="John Doe",
        )
        
        # Publish directly to Kafka
        await publisher.publish(event)
        print(f"✅ Published event directly: {event.event_type}")


# ============================================================================
# Example 2: Outbox Pattern (Reliable Publishing)
# ============================================================================

async def example_outbox_publishing():
    """
    Publishing with outbox pattern.
    
    Pros:
    - Transactional consistency with business data
    - No event loss (survives crashes)
    - Automatic retry
    
    Cons:
    - Higher latency (relay worker delay)
    - Database dependency
    - More complex setup
    """
    print("\n" + "="*80)
    print("Example 2: Outbox Pattern (Reliable Publishing)")
    print("="*80)
    
    config = get_config_outbox_only()
    
    # Initialize database
    await init_database(enable_outbox=True, enable_inbox=False)
    
    # Create session
    async with async_session_factory() as session:
        async with session.begin():
            # Simulate saving business data
            print("💾 Saving user to database...")
            
            # Create publisher with session
            publisher = create_event_publisher(config, session=session)
            
            event = UserCreatedIntegrationEvent(
                user_id=str(uuid4()),
                email="jane@example.com",
                full_name="Jane Smith",
            )
            
            # Publish to outbox (stored in database)
            await publisher.publish(event)
            print(f"✅ Saved event to outbox: {event.event_type}")
            
            # Both user and event committed atomically!
        
        print("✅ Transaction committed (user + outbox event)")
    
    # Start outbox relay to publish to Kafka
    print("\n📤 Starting outbox relay worker...")
    relay = OutboxRelay(config, async_session_factory, poll_interval_seconds=2)
    await relay.start()
    
    # Give relay time to publish
    await asyncio.sleep(5)
    
    await relay.stop()
    print("✅ Outbox relay stopped")


# ============================================================================
# Example 3: Inbox Pattern (Exactly-Once Consuming)
# ============================================================================

class UserCreatedHandler(InboxIntegrationEventHandler):
    """Handler for UserCreatedIntegrationEvent."""
    
    async def handle(self, event: UserCreatedIntegrationEvent, session: AsyncSession):
        print(f"\n📨 Processing event: {event.event_type}")
        print(f"   User ID: {event.user_id}")
        print(f"   Email: {event.email}")
        
        # Simulate sending welcome email
        print("📧 Sending welcome email...")
        await asyncio.sleep(0.5)
        
        print("✅ Welcome email sent")


async def example_inbox_consuming():
    """
    Consuming with inbox pattern.
    
    Pros:
    - Exactly-once processing (duplicate detection)
    - Transactional processing with business data
    - Survives crashes
    
    Cons:
    - Database dependency
    - Slightly higher overhead
    """
    print("\n" + "="*80)
    print("Example 3: Inbox Pattern (Exactly-Once Consuming)")
    print("="*80)
    
    config = get_config_inbox_only()
    
    # Initialize database
    await init_database(enable_outbox=False, enable_inbox=True)
    
    # Create consumer with inbox
    consumer = InboxIntegrationEventConsumer(
        kafka_config=config,
        session_factory=async_session_factory,
        store_payload=True,
    )
    
    # Register handler
    consumer.register_handler(
        UserCreatedIntegrationEvent,
        UserCreatedHandler()
    )
    
    print("👂 Starting consumer with inbox pattern...")
    await consumer.start(["users.created"])
    
    # Consume for a while
    await asyncio.sleep(10)
    
    await consumer.stop()
    print("✅ Consumer stopped")


# ============================================================================
# Example 4: Full Reliability (Both Patterns)
# ============================================================================

async def example_full_reliability():
    """
    Using both outbox and inbox patterns for maximum reliability.
    
    Producer: Outbox pattern for reliable publishing
    Consumer: Inbox pattern for exactly-once processing
    
    This is the recommended approach for production systems.
    """
    print("\n" + "="*80)
    print("Example 4: Full Reliability (Outbox + Inbox)")
    print("="*80)
    
    config = get_config_full_reliability()
    
    # Initialize database (both tables)
    await init_database(enable_outbox=True, enable_inbox=True)
    
    # === Producer Side (with Outbox) ===
    print("\n📤 PRODUCER: Publishing with outbox pattern")
    
    async with async_session_factory() as session:
        async with session.begin():
            publisher = create_event_publisher(config, session=session)
            
            event = UserCreatedIntegrationEvent(
                user_id=str(uuid4()),
                email="alice@example.com",
                full_name="Alice Johnson",
            )
            
            await publisher.publish(event)
            print(f"✅ Event saved to outbox")
    
    # Start outbox relay
    relay = OutboxRelay(config, async_session_factory, poll_interval_seconds=2)
    await relay.start()
    print("✅ Outbox relay started")
    
    # === Consumer Side (with Inbox) ===
    print("\n📨 CONSUMER: Consuming with inbox pattern")
    
    consumer = InboxIntegrationEventConsumer(
        kafka_config=config,
        session_factory=async_session_factory,
        store_payload=True,
    )
    
    consumer.register_handler(
        UserCreatedIntegrationEvent,
        UserCreatedHandler()
    )
    
    await consumer.start(["users.created"])
    print("✅ Inbox consumer started")
    
    # Let it run
    await asyncio.sleep(10)
    
    # Cleanup
    await consumer.stop()
    await relay.stop()
    print("\n✅ All components stopped")


# ============================================================================
# Example 5: Production FastAPI Integration
# ============================================================================

async def get_publisher(session: AsyncSession = Depends(get_session)):
    """Dependency that provides the right publisher based on config."""
    config = KafkaConfig()  # Loaded from environment
    return create_event_publisher(config, session=session if config.enable_outbox else None)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with conditional outbox relay."""
    config = KafkaConfig()
    
    # Initialize database
    await init_database(config.enable_outbox, config.enable_inbox)
    
    # Start outbox relay if enabled
    relay = None
    if config.enable_outbox:
        relay = OutboxRelay(config, async_session_factory)
        await relay.start()
        print("✅ Outbox relay started")
    
    # Start inbox consumer if enabled
    consumer = None
    if config.enable_inbox:
        consumer = InboxIntegrationEventConsumer(config, async_session_factory)
        # Register handlers...
        await consumer.start(["users.created"])
        print("✅ Inbox consumer started")
    
    yield
    
    # Shutdown
    if consumer:
        await consumer.stop()
    if relay:
        await relay.stop()


app = FastAPI(lifespan=lifespan)


@app.post("/users")
async def create_user(
    email: str,
    full_name: str,
    session: AsyncSession = Depends(get_session),
    publisher = Depends(get_publisher),
):
    """
    Create user endpoint.
    
    Publisher automatically uses outbox or direct publishing
    based on configuration (KAFKA_ENABLE_OUTBOX environment variable).
    """
    async with session.begin():
        # Save user (example)
        user_id = str(uuid4())
        # await user_repository.save(user)
        
        # Publish event
        event = UserCreatedIntegrationEvent(
            user_id=user_id,
            email=email,
            full_name=full_name,
        )
        await publisher.publish(event)
    
    return {"user_id": user_id}


# ============================================================================
# Main
# ============================================================================

async def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("CONFIGURABLE INBOX/OUTBOX PATTERN EXAMPLES")
    print("="*80)
    
    # Example 1: Direct (no patterns)
    await example_direct_publishing()
    
    # Example 2: Outbox only
    await example_outbox_publishing()
    
    # Example 3: Inbox only
    # await example_inbox_consuming()  # Requires Kafka
    
    # Example 4: Both patterns
    # await example_full_reliability()  # Requires Kafka
    
    print("\n" + "="*80)
    print("✅ All examples completed!")
    print("="*80)
    print("\nConfiguration Summary:")
    print("  KAFKA_ENABLE_OUTBOX=true   → Use outbox pattern for publishing")
    print("  KAFKA_ENABLE_INBOX=true    → Use inbox pattern for consuming")
    print("  Both false                 → Direct Kafka (no database)")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
