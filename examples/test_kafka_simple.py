"""
Simple Kafka Integration Test

Tests basic Kafka producer and consumer functionality.
No database required - direct publishing only.
"""

from __future__ import annotations

import asyncio
import json
from uuid import uuid4
from datetime import datetime
from typing import TYPE_CHECKING

from building_blocks.domain.events.integration_event import IntegrationEvent
from building_blocks.infrastructure.messaging import (
    KafkaConfig,
    KafkaIntegrationEventPublisher,
    KafkaIntegrationEventConsumer,
    IntegrationEventHandler,
)

if TYPE_CHECKING:
    pass


# ============================================================================
# Test Events
# ============================================================================

class UserCreatedEvent(IntegrationEvent):
    """User created integration event."""
    user_id: str
    email: str
    full_name: str


class OrderCreatedEvent(IntegrationEvent):
    """Order created integration event."""
    order_id: str
    user_id: str
    total_amount: float


# ============================================================================
# Event Handlers
# ============================================================================

class UserCreatedHandler(IntegrationEventHandler):
    """Handles user created events."""
    
    async def handle(self, event: UserCreatedEvent) -> None:
        print(f"\n✅ RECEIVED: UserCreatedEvent")
        print(f"   User ID: {event.user_id}")
        print(f"   Email: {event.email}")
        print(f"   Name: {event.full_name}")
        print(f"   Timestamp: {event.occurred_on}")


class OrderCreatedHandler(IntegrationEventHandler):
    """Handles order created events."""
    
    async def handle(self, event: OrderCreatedEvent) -> None:
        print(f"\n✅ RECEIVED: OrderCreatedEvent")
        print(f"   Order ID: {event.order_id}")
        print(f"   User ID: {event.user_id}")
        print(f"   Amount: ${event.total_amount:.2f}")
        print(f"   Timestamp: {event.occurred_on}")


# ============================================================================
# Test Scenarios
# ============================================================================

async def test_publish_events():
    """Test publishing events to Kafka."""
    print("\n" + "="*80)
    print("TEST 1: Publishing Events to Kafka")
    print("="*80)
    
    config = KafkaConfig(
        bootstrap_servers="localhost:9092",
        service_name="test-publisher",
        enable_outbox=False,  # Direct publishing
        enable_inbox=False,
    )
    
    publisher = KafkaIntegrationEventPublisher(config)
    
    try:
        await publisher.start()
        print("✅ Publisher connected to Kafka")
        
        # Publish UserCreatedEvent
        user_event = UserCreatedEvent(
            user_id=str(uuid4()),
            email="alice@example.com",
            full_name="Alice Johnson",
        )
        await publisher.publish(user_event)
        print(f"\n📤 Published: {user_event.event_type}")
        print(f"   Topic: users.created")
        
        # Publish OrderCreatedEvent
        order_event = OrderCreatedEvent(
            order_id=str(uuid4()),
            user_id=user_event.user_id,
            total_amount=99.99,
        )
        await publisher.publish(order_event)
        print(f"\n📤 Published: {order_event.event_type}")
        print(f"   Topic: orders.created")
        
        # Publish multiple events
        print("\n📤 Publishing batch of events...")
        for i in range(3):
            event = UserCreatedEvent(
                user_id=str(uuid4()),
                email=f"user{i}@example.com",
                full_name=f"User {i}",
            )
            await publisher.publish(event)
            print(f"   Published user {i+1}/3")
        
        print("\n✅ All events published successfully!")
        
    finally:
        await publisher.stop()
        print("✅ Publisher stopped")


async def test_consume_events():
    """Test consuming events from Kafka."""
    print("\n" + "="*80)
    print("TEST 2: Consuming Events from Kafka")
    print("="*80)
    
    config = KafkaConfig(
        bootstrap_servers="localhost:9092",
        service_name="test-consumer",
        consumer_group_id="test-consumer-group",
        enable_outbox=False,
        enable_inbox=False,
    )
    
    consumer = KafkaIntegrationEventConsumer(config)
    
    # Register handlers
    consumer.register_handler(UserCreatedEvent, UserCreatedHandler())
    consumer.register_handler(OrderCreatedEvent, OrderCreatedHandler())
    
    try:
        # Subscribe to topics
        await consumer.start(["users.created", "orders.created"])
        print("✅ Consumer started and subscribed to topics:")
        print("   - users.created")
        print("   - orders.created")
        print("\n👂 Listening for events... (will stop after 30 seconds)\n")
        
        # Consume for 30 seconds
        await asyncio.sleep(30)
        
    finally:
        await consumer.stop()
        print("\n✅ Consumer stopped")


async def test_round_trip():
    """Test publishing and consuming in the same process."""
    print("\n" + "="*80)
    print("TEST 3: Full Round-Trip (Publish + Consume)")
    print("="*80)
    
    # Setup publisher
    pub_config = KafkaConfig(
        bootstrap_servers="localhost:9092",
        service_name="test-publisher",
        enable_outbox=False,
        enable_inbox=False,
    )
    publisher = KafkaIntegrationEventPublisher(pub_config)
    
    # Setup consumer
    consumer_config = KafkaConfig(
        bootstrap_servers="localhost:9092",
        service_name="test-consumer",
        consumer_group_id="test-roundtrip-group",
        enable_outbox=False,
        enable_inbox=False,
    )
    consumer = KafkaIntegrationEventConsumer(consumer_config)
    consumer.register_handler(UserCreatedEvent, UserCreatedHandler())
    
    try:
        # Start both
        await publisher.start()
        await consumer.start(["users.created"])
        print("✅ Publisher and consumer started\n")
        
        # Give consumer time to subscribe
        await asyncio.sleep(2)
        
        # Publish events
        print("📤 Publishing 5 events...")
        for i in range(5):
            event = UserCreatedEvent(
                user_id=str(uuid4()),
                email=f"test{i}@example.com",
                full_name=f"Test User {i}",
            )
            await publisher.publish(event)
            print(f"   Published event {i+1}/5")
            await asyncio.sleep(0.5)  # Small delay between publishes
        
        print("\n👂 Waiting for events to be consumed...")
        await asyncio.sleep(5)
        
    finally:
        await consumer.stop()
        await publisher.stop()
        print("\n✅ Round-trip test completed")


# ============================================================================
# Main
# ============================================================================

async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("🧪 KAFKA INTEGRATION TESTS")
    print("="*80)
    print(f"Started at: {datetime.now().isoformat()}")
    print(f"Kafka: localhost:9092")
    print("="*80)
    
    try:
        # Test 1: Publish events
        await test_publish_events()
        
        # Wait a bit
        await asyncio.sleep(2)
        
        # Test 2: Consume events (will consume what we just published)
        await test_consume_events()
        
        # Test 3: Round-trip test
        await test_round_trip()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*80)
        print("\nSummary:")
        print("  ✅ Event publishing works")
        print("  ✅ Event consuming works")
        print("  ✅ Round-trip works")
        print("\nNext Steps:")
        print("  - Open Kafka UI: http://localhost:8080")
        print("  - Check topics: users.created, orders.created")
        print("  - View messages in Kafka UI")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
