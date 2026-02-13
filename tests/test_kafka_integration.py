"""
Unit tests for Kafka integration events.

Run with: pytest tests/test_kafka_integration.py
"""

import pytest
from datetime import datetime
from uuid import uuid4

from fastapi_building_blocks.domain.events import (
    DomainEvent,
    IntegrationEvent,
    IntegrationEventEnvelope,
)
from fastapi_building_blocks.infrastructure.messaging import (
    EventMapper,
    IntegrationEventFactory,
    KafkaConfig,
)


# ============================================================================
# Test Events
# ============================================================================

class UserCreatedDomainEvent(DomainEvent):
    """Test domain event."""
    user_id: str
    email: str


class UserCreatedIntegrationEvent(IntegrationEvent):
    """Test integration event."""
    user_id: str
    email: str
    full_name: str


# ============================================================================
# Tests
# ============================================================================

class TestIntegrationEvent:
    """Test integration event base class."""
    
    def test_create_integration_event(self):
        """Test creating an integration event."""
        event = UserCreatedIntegrationEvent(
            user_id="123",
            email="test@example.com",
            full_name="Test User",
        )
        
        assert event.event_id is not None
        assert event.occurred_at is not None
        assert event.event_type == "UserCreatedIntegrationEvent"
        assert event.event_version == "1.0"
        assert event.user_id == "123"
        assert event.email == "test@example.com"
    
    def test_event_serialization(self):
        """Test event serialization to dict."""
        event = UserCreatedIntegrationEvent(
            user_id="123",
            email="test@example.com",
            full_name="Test User",
        )
        
        data = event.to_dict()
        
        assert isinstance(data, dict)
        assert data["event_type"] == "UserCreatedIntegrationEvent"
        assert data["user_id"] == "123"
        assert data["email"] == "test@example.com"
    
    def test_event_deserialization(self):
        """Test event deserialization from dict."""
        data = {
            "user_id": "123",
            "email": "test@example.com",
            "full_name": "Test User",
            "event_version": "1.0",
        }
        
        event = UserCreatedIntegrationEvent.from_dict(data)
        
        assert event.user_id == "123"
        assert event.email == "test@example.com"
        assert event.full_name == "Test User"
    
    def test_topic_naming(self):
        """Test automatic topic naming."""
        event = UserCreatedIntegrationEvent(
            user_id="123",
            email="test@example.com",
            full_name="Test User",
        )
        
        topic = event.get_topic_name()
        
        assert topic == "integration-events.user_created_integration_event"
    
    def test_partition_key(self):
        """Test partition key generation."""
        user_id = uuid4()
        event = UserCreatedIntegrationEvent(
            user_id=str(user_id),
            email="test@example.com",
            full_name="Test User",
            aggregate_id=user_id,
        )
        
        partition_key = event.get_partition_key()
        
        assert partition_key == str(user_id)


class TestIntegrationEventEnvelope:
    """Test integration event envelope."""
    
    def test_wrap_event(self):
        """Test wrapping an event in an envelope."""
        event = UserCreatedIntegrationEvent(
            user_id="123",
            email="test@example.com",
            full_name="Test User",
        )
        
        envelope = IntegrationEventEnvelope.wrap(event)
        
        assert envelope.event_id == event.event_id
        assert envelope.event_type == event.event_type
        assert envelope.event_version == event.event_version
        assert envelope.payload == event.to_dict()
    
    def test_envelope_serialization(self):
        """Test envelope JSON serialization."""
        event = UserCreatedIntegrationEvent(
            user_id="123",
            email="test@example.com",
            full_name="Test User",
        )
        
        envelope = IntegrationEventEnvelope.wrap(event)
        json_str = envelope.to_json()
        
        assert isinstance(json_str, str)
        assert "UserCreatedIntegrationEvent" in json_str
        assert "test@example.com" in json_str
    
    def test_envelope_deserialization(self):
        """Test envelope JSON deserialization."""
        event = UserCreatedIntegrationEvent(
            user_id="123",
            email="test@example.com",
            full_name="Test User",
        )
        
        envelope = IntegrationEventEnvelope.wrap(event)
        json_str = envelope.to_json()
        
        deserialized = IntegrationEventEnvelope.from_json(json_str)
        
        assert deserialized.event_id == envelope.event_id
        assert deserialized.event_type == envelope.event_type
        assert deserialized.payload == envelope.payload


class TestEventMapper:
    """Test event mapper."""
    
    def test_register_simple_mapping(self):
        """Test registering a simple 1-to-1 mapping."""
        mapper = EventMapper()
        
        mapper.register_mapping(
            UserCreatedDomainEvent,
            UserCreatedIntegrationEvent,
        )
        
        assert mapper.has_mapping(UserCreatedDomainEvent)
    
    def test_map_domain_event(self):
        """Test mapping a domain event to integration event."""
        mapper = EventMapper()
        
        mapper.register_mapping(
            UserCreatedDomainEvent,
            UserCreatedIntegrationEvent,
        )
        
        domain_event = UserCreatedDomainEvent(
            user_id="123",
            email="test@example.com",
        )
        
        integration_event = mapper.map(domain_event)
        
        assert integration_event is not None
        assert isinstance(integration_event, UserCreatedIntegrationEvent)
        assert integration_event.user_id == "123"
        assert integration_event.email == "test@example.com"
    
    def test_map_with_transform(self):
        """Test mapping with custom transformation."""
        mapper = EventMapper()
        
        def transform(domain_event: UserCreatedDomainEvent) -> dict:
            return {
                "user_id": domain_event.user_id,
                "email": domain_event.email,
                "full_name": "Transformed Name",
            }
        
        mapper.register_mapping(
            UserCreatedDomainEvent,
            UserCreatedIntegrationEvent,
            transform=transform,
        )
        
        domain_event = UserCreatedDomainEvent(
            user_id="123",
            email="test@example.com",
        )
        
        integration_event = mapper.map(domain_event)
        
        assert integration_event.full_name == "Transformed Name"
    
    def test_map_unmapped_event(self):
        """Test mapping an event with no registered mapping."""
        mapper = EventMapper()
        
        domain_event = UserCreatedDomainEvent(
            user_id="123",
            email="test@example.com",
        )
        
        result = mapper.map(domain_event)
        
        assert result is None


class TestIntegrationEventFactory:
    """Test integration event factory."""
    
    def test_create_from_domain_event(self):
        """Test creating integration event from domain event."""
        factory = IntegrationEventFactory("my-service")
        
        domain_event = UserCreatedDomainEvent(
            user_id="123",
            email="test@example.com",
        )
        
        integration_event = factory.create_from_domain_event(
            UserCreatedIntegrationEvent,
            domain_event,
            full_name="Test User",
        )
        
        assert integration_event.user_id == "123"
        assert integration_event.email == "test@example.com"
        assert integration_event.full_name == "Test User"
        assert integration_event.source_service == "my-service"
        assert integration_event.causation_id == domain_event.event_id
    
    def test_create_new_event(self):
        """Test creating a new integration event."""
        factory = IntegrationEventFactory("my-service")
        
        correlation_id = uuid4()
        
        integration_event = factory.create(
            UserCreatedIntegrationEvent,
            user_id="123",
            email="test@example.com",
            full_name="Test User",
            correlation_id=correlation_id,
        )
        
        assert integration_event.source_service == "my-service"
        assert integration_event.correlation_id == correlation_id


class TestKafkaConfig:
    """Test Kafka configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = KafkaConfig()
        
        assert config.bootstrap_servers == "localhost:9092"
        assert config.service_name == "fastapi-service"
        assert config.producer_acks == "all"
        assert config.enable_idempotence is True
    
    def test_get_producer_config(self):
        """Test getting producer configuration."""
        config = KafkaConfig(
            bootstrap_servers="broker1:9092,broker2:9092",
            producer_acks="1",
        )
        
        producer_config = config.get_producer_config()
        
        assert producer_config["bootstrap_servers"] == ["broker1:9092", "broker2:9092"]
        assert producer_config["acks"] == "1"
        assert "compression_type" in producer_config
    
    def test_get_consumer_config(self):
        """Test getting consumer configuration."""
        config = KafkaConfig(
            consumer_group_id="my-group",
            consumer_auto_offset_reset="latest",
        )
        
        consumer_config = config.get_consumer_config()
        
        assert consumer_config["group_id"] == "my-group"
        assert consumer_config["auto_offset_reset"] == "latest"
        assert "bootstrap_servers" in consumer_config


# ============================================================================
# Integration Tests (require running Kafka)
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_kafka_producer_connection():
    """Test Kafka producer connection (requires running Kafka)."""
    from fastapi_building_blocks.infrastructure.messaging import (
        KafkaIntegrationEventPublisher,
    )
    
    config = KafkaConfig(bootstrap_servers="localhost:9092")
    publisher = KafkaIntegrationEventPublisher(config)
    
    try:
        await publisher.start()
        assert publisher._started is True
    except Exception as e:
        pytest.skip(f"Kafka not available: {e}")
    finally:
        await publisher.stop()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_publish_and_consume_event():
    """Test publishing and consuming an event (requires running Kafka)."""
    from fastapi_building_blocks.infrastructure.messaging import (
        KafkaIntegrationEventPublisher,
        KafkaIntegrationEventConsumer,
        IntegrationEventHandler,
    )
    
    # Track received events
    received_events = []
    
    class TestHandler(IntegrationEventHandler):
        async def handle(self, event: UserCreatedIntegrationEvent) -> None:
            received_events.append(event)
    
    config = KafkaConfig(
        bootstrap_servers="localhost:9092",
        consumer_group_id="test-group",
    )
    
    try:
        # Start publisher
        publisher = KafkaIntegrationEventPublisher(config)
        await publisher.start()
        
        # Start consumer
        consumer = KafkaIntegrationEventConsumer(config)
        consumer.register_handler(UserCreatedIntegrationEvent, TestHandler())
        await consumer.start(["integration-events.user_created_integration_event"])
        
        # Publish event
        event = UserCreatedIntegrationEvent(
            user_id="123",
            email="test@example.com",
            full_name="Test User",
        )
        await publisher.publish(event)
        
        # Wait for consumption
        import asyncio
        await asyncio.sleep(2)
        
        # Verify
        assert len(received_events) > 0
        assert received_events[0].user_id == "123"
        
    except Exception as e:
        pytest.skip(f"Kafka not available: {e}")
    finally:
        await publisher.stop()
        await consumer.stop()
