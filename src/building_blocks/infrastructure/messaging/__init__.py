"""Messaging components."""

from .base import IEventPublisher, IMessageBus
from .kafka_config import KafkaConfig
from .kafka_producer import KafkaIntegrationEventPublisher
from .kafka_consumer import KafkaIntegrationEventConsumer, IntegrationEventHandler
from .event_mapper import EventMapper, IntegrationEventFactory
from .integration_middleware import (
    IntegrationEventPublishingBehavior,
    IntegrationEventMediatorWrapper,
    create_integration_event_mediator,
)
# Inbox/Outbox pattern
from .outbox_publisher import OutboxEventPublisher, OutboxEventPublisherFactory
from .outbox_relay import OutboxRelay
from .inbox_consumer import InboxIntegrationEventConsumer, InboxIntegrationEventHandler
from .publisher_factory import (
    IntegrationEventPublisherFactory,
    create_event_publisher,
)

__all__ = [
    # Base interfaces
    "IEventPublisher",
    "IMessageBus",
    # Kafka configuration
    "KafkaConfig",
    # Kafka producer/consumer (direct)
    "KafkaIntegrationEventPublisher",
    "KafkaIntegrationEventConsumer",
    "IntegrationEventHandler",
    # Event mapping and transformation
    "EventMapper",
    "IntegrationEventFactory",
    # Integration with mediator
    "IntegrationEventPublishingBehavior",
    "IntegrationEventMediatorWrapper",
    "create_integration_event_mediator",
    # Inbox/Outbox pattern
    "OutboxEventPublisher",
    "OutboxEventPublisherFactory",
    "OutboxRelay",
    "InboxIntegrationEventConsumer",
    "InboxIntegrationEventHandler",
    # Publisher factory
    "IntegrationEventPublisherFactory",
    "create_event_publisher",
]
