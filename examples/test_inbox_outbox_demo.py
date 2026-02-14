"""
Inbox/Outbox Pattern Demo

Demonstrates the inbox and outbox patterns with actual database tables.
Shows how events are stored and processed reliably.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
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
from building_blocks.infrastructure.persistence.outbox import (
    OutboxRepository,
    CREATE_OUTBOX_TABLE_SQL,
)
from building_blocks.infrastructure.persistence.inbox import (
    InboxRepository,
    CREATE_INBOX_TABLE_SQL,
)


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
    """Handles user created events with inbox pattern."""
    
    async def handle(self, event: UserCreatedEvent) -> None:
        print(f"\n✅ PROCESSED (via Inbox): UserCreatedEvent")
        print(f"   User ID: {event.user_id}")
        print(f"   Email: {event.email}")
        print(f"   Name: {event.full_name}")
        # Simulate processing (e.g., send welcome email)
        await asyncio.sleep(0.1)
        print(f"   📧 Welcome email sent!")


class OrderPlacedHandler(InboxIntegrationEventHandler):
    """Handles order placed events with inbox pattern."""
    
    async def handle(self, event: OrderPlacedEvent) -> None:
        print(f"\n✅ PROCESSED (via Inbox): OrderPlacedEvent")
        print(f"   Order ID: {event.order_id}")
        print(f"   User ID: {event.user_id}")
        print(f"   Amount: ${event.total_amount:.2f}")
        # Simulate processing (e.g., send order confirmation)
        await asyncio.sleep(0.1)
        print(f"   📦 Order confirmation sent!")


# ============================================================================
# Database Setup
# ============================================================================

# Use the running PostgreSQL container
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/user_management"

async_engine = create_async_engine(DATABASE_URL, echo=False)
async_session_factory = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_tables():
    """Initialize inbox and outbox tables."""
    print("\n" + "="*80)
    print("📦 Initializing Database Tables")
    print("="*80)
    
    from sqlalchemy import text
    
    async with async_engine.begin() as conn:
        # Create outbox table
        await conn.execute(text(CREATE_OUTBOX_TABLE_SQL))
        print("✅ Created outbox_messages table")
        
        # Create inbox table
        await conn.execute(text(CREATE_INBOX_TABLE_SQL))
        print("✅ Created inbox_messages table")


async def show_outbox_messages():
    """Display messages in the outbox table."""
    async with async_session_factory() as session:
        repo = OutboxRepository(session)
        messages = await repo.get_pending_messages(limit=100)
        
        print(f"\n📤 OUTBOX MESSAGES ({len(messages)} total):")
        print("-" * 80)
        if messages:
            for msg in messages:
                print(f"  ID: {msg.id}")
                print(f"  Event Type: {msg.event_type}")
                print(f"  Topic: {msg.topic}")
                print(f"  Status: {msg.status}")
                print(f"  Created: {msg.created_at}")
                if msg.published_at:
                    print(f"  Published: {msg.published_at}")
                print("-" * 80)
        else:
            print("  (no pending messages)")


async def show_inbox_messages():
    """Display messages in the inbox table."""
    async with async_session_factory() as session:
        from sqlalchemy import text
        result = await session.execute(
            text("SELECT id, event_id, event_type, topic, processed, created_at FROM inbox_messages ORDER BY created_at DESC LIMIT 10")
        )
        messages = result.fetchall()
        
        print(f"\n📥 INBOX MESSAGES ({len(messages)} total):")
        print("-" * 80)
        if messages:
            for msg in messages:
                print(f"  ID: {msg[0]}")
                print(f"  Event ID: {msg[1]}")
                print(f"  Event Type: {msg[2]}")
                print(f"  Topic: {msg[3]}")
                print(f"  Processed: {msg[4]}")
                print(f"  Created: {msg[5]}")
                print("-" * 80)
        else:
            print("  (no messages)")


# ============================================================================
# Demo Scenarios
# ============================================================================

async def demo_outbox_publishing():
    """Demo: Publishing events through the outbox pattern."""
    print("\n" + "="*80)
    print("DEMO 1: Outbox Pattern - Transactional Publishing")
    print("="*80)
    print("\n📝 Publishing events to outbox (stored in database)...")
    
    config = KafkaConfig(
        bootstrap_servers="localhost:9092",
        service_name="user-service",
        enable_outbox=True,
    )
    
    # Publish events in a transaction
    async with async_session_factory() as session:
        async with session.begin():
            publisher = OutboxEventPublisher(config, session)
            
            # Event 1: User created
            user_event = UserCreatedEvent(
                user_id=str(uuid4()),
                email="john.doe@example.com",
                full_name="John Doe",
            )
            await publisher.publish(user_event)
            print(f"✅ Saved to outbox: {user_event.event_type}")
            
            # Event 2: Another user
            user_event2 = UserCreatedEvent(
                user_id=str(uuid4()),
                email="jane.smith@example.com",
                full_name="Jane Smith",
            )
            await publisher.publish(user_event2)
            print(f"✅ Saved to outbox: {user_event2.event_type}")
            
            # Event 3: Order placed
            order_event = OrderPlacedEvent(
                order_id=str(uuid4()),
                user_id=user_event.user_id,
                total_amount=149.99,
            )
            await publisher.publish(order_event)
            print(f"✅ Saved to outbox: {order_event.event_type}")
            
        print("\n✅ Transaction committed - all events saved to outbox")
    
    # Show outbox contents
    await show_outbox_messages()


async def demo_outbox_relay():
    """Demo: Outbox relay worker publishing events to Kafka."""
    print("\n" + "="*80)
    print("DEMO 2: Outbox Relay - Publishing to Kafka")
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
        
        print("\n⏳ Processing outbox messages (10 seconds)...")
        await asyncio.sleep(10)
        
    finally:
        await relay.stop()
        print("\n✅ Relay worker stopped")
    
    # Show updated outbox contents
    await show_outbox_messages()


async def demo_inbox_consuming():
    """Demo: Consuming events through the inbox pattern."""
    print("\n" + "="*80)
    print("DEMO 3: Inbox Pattern - Exactly-Once Processing")
    print("="*80)
    
    config = KafkaConfig(
        bootstrap_servers="localhost:9092",
        service_name="email-service",
        consumer_group_id="email-service-group-demo",
        enable_inbox=True,
    )
    
    consumer = InboxIntegrationEventConsumer(config, async_session_factory, enable_inbox=True)
    
    # Register handlers
    consumer.register_handler(UserCreatedEvent, UserCreatedHandler())
    consumer.register_handler(OrderPlacedEvent, OrderPlacedHandler())
    
    try:
        print("\n📥 Starting inbox consumer...")
        await consumer.start(["users.created", "orders.placed"])
        print("✅ Consumer started and subscribed")
        
        print("\n👂 Listening for events (15 seconds)...")
        await asyncio.sleep(15)
        
    finally:
        await consumer.stop()
        print("\n✅ Consumer stopped")
    
    # Show inbox contents
    await show_inbox_messages()


async def demo_duplicate_detection():
    """Demo: Inbox prevents duplicate processing."""
    print("\n" + "="*80)
    print("DEMO 4: Duplicate Detection")
    print("="*80)
    
    print("\n🔄 Restarting consumer to test duplicate detection...")
    
    config = KafkaConfig(
        bootstrap_servers="localhost:9092",
        service_name="email-service",
        consumer_group_id="email-service-group-demo",
        enable_inbox=True,
    )
    
    consumer = InboxIntegrationEventConsumer(config, async_session_factory, enable_inbox=True)
    consumer.register_handler(UserCreatedEvent, UserCreatedHandler())
    consumer.register_handler(OrderPlacedEvent, OrderPlacedHandler())
    
    try:
        await consumer.start(["users.created", "orders.placed"])
        print("✅ Consumer started")
        
        print("\n⏳ Processing (should skip already processed events)...")
        await asyncio.sleep(10)
        
    finally:
        await consumer.stop()
        print("\n✅ Consumer stopped")
    
    await show_inbox_messages()


# ============================================================================
# Main
# ============================================================================

async def main():
    """Run all demos."""
    print("\n" + "="*80)
    print("🎯 INBOX/OUTBOX PATTERN DEMONSTRATION")
    print("="*80)
    print(f"Started at: {datetime.now().isoformat()}")
    print(f"Database: {DATABASE_URL}")
    print(f"Kafka: localhost:9092")
    print("="*80)
    
    try:
        # Step 1: Initialize tables
        await init_tables()
        
        # Step 2: Demo outbox publishing
        await demo_outbox_publishing()
        
        # Step 3: Demo outbox relay
        await demo_outbox_relay()
        
        # Step 4: Demo inbox consuming
        await demo_inbox_consuming()
        
        # Step 5: Demo duplicate detection
        await demo_duplicate_detection()
        
        print("\n" + "="*80)
        print("✅ ALL DEMOS COMPLETED!")
        print("="*80)
        print("\nWhat happened:")
        print("  1. ✅ Created outbox_messages and inbox_messages tables")
        print("  2. ✅ Saved 3 events to outbox (transactional)")
        print("  3. ✅ Relay worker published events to Kafka")
        print("  4. ✅ Inbox consumer processed events (exactly-once)")
        print("  5. ✅ Duplicate detection prevented reprocessing")
        print("\nVerify in database:")
        print("  docker exec -it user-management-db psql -U user -d mydb")
        print("  SELECT * FROM outbox_messages;")
        print("  SELECT * FROM inbox_messages;")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
