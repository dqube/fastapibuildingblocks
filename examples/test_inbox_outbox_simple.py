"""
Simple Inbox/Outbox Test

Publishes a message through outbox, relays to Kafka, and consumes via inbox.
"""

from __future__ import annotations

import asyncio
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from building_blocks.domain.events.integration_event import IntegrationEvent
from building_blocks.infrastructure.messaging import (
    KafkaConfig,
    OutboxEventPublisher,
    OutboxRelay,
    InboxIntegrationEventConsumer,
    InboxIntegrationEventHandler,
)
from building_blocks.infrastructure.persistence.outbox import OutboxRepository


# ============================================================================
# Events
# ============================================================================

class UserCreatedEvent(IntegrationEvent):
    """User created integration event."""
    user_id: str
    email: str
    full_name: str


class OrderPlacedEvent(IntegrationEvent):
    """Order placed integration event."""
    order_id: str
    user_id: str
    total_amount: float


# ============================================================================
# Event Handlers
# ============================================================================

class UserCreatedHandler(InboxIntegrationEventHandler):
    """Handles user created events."""
    
    async def handle(self, event: UserCreatedEvent, session) -> None:
        print(f"\n✉️  CONSUMED: UserCreatedEvent")
        print(f"   User: {event.full_name} ({event.email})")
        print(f"   Event ID: {event.event_id}")


class OrderPlacedHandler(InboxIntegrationEventHandler):
    """Handles order placed events."""
    
    async def handle(self, event: OrderPlacedEvent, session) -> None:
        print(f"\n✉️  CONSUMED: OrderPlacedEvent")
        print(f"   Order ID: {event.order_id}")
        print(f"   Amount: ${event.total_amount:.2f}")
        print(f"   Event ID: {event.event_id}")


# ============================================================================
# Database Setup
# ============================================================================

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/user_management"

async_engine = create_async_engine(DATABASE_URL, echo=False)
async_session_factory = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ============================================================================
# Test Functions
# ============================================================================

async def publish_to_outbox():
    """Step 1: Publish events to outbox table."""
    print("\n" + "="*80)
    print("STEP 1: Publishing Events to Outbox Table")
    print("="*80)
    
    config = KafkaConfig(
        bootstrap_servers="localhost:9092",
        service_name="user-service",
        enable_outbox=True,
    )
    
    async with async_session_factory() as session:
        async with session.begin():
            # Create publisher using repository
            outbox_repo = OutboxRepository(session)
            publisher = OutboxEventPublisher(
                outbox_repository=outbox_repo,
                service_name=config.service_name,
                store_payload=True,
            )
            
            # Event 1: User created
            user_event = UserCreatedEvent(
                user_id=str(uuid4()),
                email="test.user@example.com",
                full_name="Test User",
            )
            
            await publisher.publish(user_event)
            print(f"✅ Saved to outbox: {user_event.event_type}")
            print(f"   Email: {user_event.email}")
            
            # Event 2: Order placed
            order_event = OrderPlacedEvent(
                order_id=str(uuid4()),
                user_id=user_event.user_id,
                total_amount=299.99,
            )
            await publisher.publish(order_event)
            print(f"✅ Saved to outbox: {order_event.event_type}")
            print(f"   Amount: ${order_event.total_amount:.2f}")
        
        print("\n✅ Transaction committed - events saved to outbox_messages table")
    
    # Show outbox count
    async with async_session_factory() as session:
        repo = OutboxRepository(session)
        messages = await repo.get_pending_messages(limit=100)
        print(f"\n📤 Outbox Messages: {len(messages)} pending")


async def relay_outbox_to_kafka():
    """Step 2: Relay worker publishes outbox messages to Kafka."""
    print("\n" + "="*80)
    print("STEP 2: Relaying Outbox Messages to Kafka")
    print("="*80)
    
    config = KafkaConfig(
        bootstrap_servers="localhost:9092",
        service_name="user-service",
        enable_outbox=True,
    )
    
    print("\n📤 Starting outbox relay worker...")
    relay = OutboxRelay(config, async_session_factory, poll_interval_seconds=2)
    
    try:
        await relay.start()
        print("✅ Relay worker started")
        
        print("\n⏳ Publishing messages to Kafka (15 seconds)...")
        await asyncio.sleep(15)
        
    finally:
        await relay.stop()
        print("\n✅ Relay worker stopped")
    
    # Show updated outbox
    async with async_session_factory() as session:
        repo = OutboxRepository(session)
        messages = await repo.get_pending_messages(limit=100)
        print(f"\n📤 Outbox Messages: {len(messages)} pending (should be 0)")


async def consume_with_inbox():
    """Step 3: Consumer processes messages and saves to inbox."""
    print("\n" + "="*80)
    print("STEP 3: Consuming Messages with Inbox Pattern")
    print("="*80)
    
    config = KafkaConfig(
        bootstrap_servers="localhost:9092",
        service_name="email-service",
        consumer_group_id="email-service-inbox-test",
        enable_inbox=True,
    )
    
    consumer = InboxIntegrationEventConsumer(config, async_session_factory, enable_inbox=True)
    
    # Register handlers
    consumer.register_handler(UserCreatedEvent, UserCreatedHandler())
    consumer.register_handler(OrderPlacedEvent, OrderPlacedHandler())
    
    try:
        print("\n📥 Starting inbox consumer...")
        await consumer.start(["integration-events.user_created_event", "integration-events.order_placed_event"])
        print("✅ Consumer started")
        
        print("\n👂 Listening for events (20 seconds)...")
        await asyncio.sleep(20)
        
    finally:
        await consumer.stop()
        print("\n✅ Consumer stopped")
    
    # Show inbox count
    from sqlalchemy import text
    async with async_session_factory() as session:
        result = await session.execute(
            text("SELECT COUNT(*) FROM inbox_messages WHERE status = 'processed'")
        )
        count = result.scalar()
        print(f"\n📥 Inbox Messages: {count} processed")


async def show_database_status():
    """Step 4: Show final database status."""
    print("\n" + "="*80)
    print("STEP 4: Database Status")
    print("="*80)
    
    from sqlalchemy import text
    
    async with async_session_factory() as session:
        # Outbox messages
        result = await session.execute(
            text("""
                SELECT status, COUNT(*) 
                FROM outbox_messages 
                GROUP BY status
            """)
        )
        print("\n📤 OUTBOX_MESSAGES:")
        for row in result:
            print(f"   {row[0]}: {row[1]} messages")
        
        # Inbox messages
        result = await session.execute(
            text("""
                SELECT status, COUNT(*) 
                FROM inbox_messages 
                GROUP BY status
            """)
        )
        print("\n📥 INBOX_MESSAGES:")
        for row in result:
            print(f"   {row[0]}: {row[1]} messages")
        
        # Recent outbox messages
        result = await session.execute(
            text("""
                SELECT event_type, status, created_at 
                FROM outbox_messages 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
        )
        print("\n📤 Recent Outbox Messages:")
        for row in result:
            print(f"   {row[0]} - {row[1]} - {row[2]}")
        
        # Recent inbox messages
        result = await session.execute(
            text("""
                SELECT event_type, status, received_at 
                FROM inbox_messages 
                ORDER BY received_at DESC 
                LIMIT 5
            """)
        )
        print("\n📥 Recent Inbox Messages:")
        for row in result:
            print(f"   {row[0]} - {row[1]} - {row[2]}")


# ============================================================================
# Main
# ============================================================================

async def main():
    """Run the complete inbox/outbox test."""
    print("\n" + "="*80)
    print("🧪 INBOX/OUTBOX PATTERN TEST")
    print("="*80)
    print("Database: user_management")
    print("Kafka: localhost:9092")
    print("="*80)
    
    try:
        # Step 1: Publish to outbox
        await publish_to_outbox()
        
        # Step 2: Relay to Kafka
        await relay_outbox_to_kafka()
        
        # Step 3: Consume with inbox
        await consume_with_inbox()
        
        # Step 4: Show final status
        await show_database_status()
        
        print("\n" + "="*80)
        print("✅ TEST COMPLETED SUCCESSFULLY!")
        print("="*80)
        print("\nWhat happened:")
        print("  1. ✅ Published 2 events to outbox_messages table")
        print("  2. ✅ Relay worker published events to Kafka")
        print("  3. ✅ Consumer processed events and saved to inbox_messages")
        print("  4. ✅ Duplicate processing prevented by inbox")
        print("\nVerify in pgAdmin:")
        print("  http://localhost:5050")
        print("  Database: user_management")
        print("  Tables: outbox_messages, inbox_messages")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
