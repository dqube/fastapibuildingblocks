"""
Outbox-based integration event publisher.

This publisher stores integration events in a database outbox table instead of
publishing directly to Kafka. A separate relay worker reads from the outbox
and publishes to Kafka, ensuring reliable event delivery.
"""

import json
import logging
from typing import List, Optional
from uuid import UUID

from ...domain.events.integration_event import IntegrationEvent, IntegrationEventEnvelope
from .base import IEventPublisher
from ..persistence.outbox import OutboxMessage, OutboxRepository


# Import observability modules (optional)
try:
    from ...observability.logging import get_logger
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False
    get_logger = None


logger = get_logger(__name__) if OBSERVABILITY_AVAILABLE else logging.getLogger(__name__)


class OutboxEventPublisher(IEventPublisher):
    """
    Outbox-based event publisher.
    
    Instead of publishing directly to Kafka, this publisher stores events
    in the outbox table. A separate relay worker reads from the outbox
    and publishes to Kafka.
    
    Benefits:
    - Ensures events are not lost if service crashes before publishing
    - Allows atomic commits with business data (same transaction)
    - Enables transactional outbox pattern
    - Provides retry mechanism for failed publishes
    
    Example:
        >>> repository = OutboxRepository(session)
        >>> publisher = OutboxEventPublisher(repository, "my-service")
        >>> 
        >>> # In a transaction with business data
        >>> async with session.begin():
        >>>     # Save business data
        >>>     await user_repository.save(user)
        >>>     
        >>>     # Save integration event to outbox (same transaction!)
        >>>     await publisher.publish(UserCreatedIntegrationEvent(...))
        >>>     
        >>>     # Both committed atomically
    """
    
    def __init__(
        self,
        outbox_repository: OutboxRepository,
        service_name: str,
        store_payload: bool = True,
    ):
        """
        Initialize the outbox publisher.
        
        Args:
            outbox_repository: Repository for outbox operations
            service_name: Name of this service (for metadata)
            store_payload: Whether to store full payload in outbox (for debugging)
        """
        self.outbox_repository = outbox_repository
        self.service_name = service_name
        self.store_payload = store_payload
    
    async def publish(self, event: IntegrationEvent) -> None:
        """
        Publish an integration event to the outbox.
        
        The event is stored in the outbox table and will be published
        to Kafka by the relay worker.
        
        Args:
            event: The integration event to publish
        """
        # Set source service if not already set
        if not event.source_service:
            event.source_service = self.service_name
        
        # Get topic and partition key
        topic = event.get_topic_name()
        partition_key = event.get_partition_key()
        
        # Wrap event in envelope
        envelope = IntegrationEventEnvelope.wrap(event)
        
        # Prepare headers
        headers = {
            "event_type": event.event_type,
            "event_id": str(event.event_id),
            "event_version": event.event_version,
            "correlation_id": str(event.correlation_id) if event.correlation_id else "",
            "source_service": event.source_service or "",
        }
        
        # Create outbox message
        outbox_message = OutboxMessage(
            event_id=event.event_id,
            event_type=event.event_type,
            event_version=event.event_version,
            topic=topic,
            partition_key=partition_key,
            payload=envelope.to_json(),
            headers=json.dumps(headers),
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            source_service=event.source_service,
            aggregate_id=event.aggregate_id,
        )
        
        # Save to outbox
        await self.outbox_repository.add(outbox_message)
        
        if logger:
            logger.info(
                f"Saved integration event to outbox: {event.event_type}",
                extra={
                    "extra_fields": {
                        "event.type": event.event_type,
                        "event.id": str(event.event_id),
                        "outbox.topic": topic,
                        "outbox.message_id": str(outbox_message.id),
                    }
                },
            )
    
    async def publish_many(self, events: List[IntegrationEvent]) -> None:
        """
        Publish multiple integration events to the outbox.
        
        Args:
            events: List of integration events to publish
        """
        if not events:
            return
        
        outbox_messages = []
        
        for event in events:
            # Set source service if not already set
            if not event.source_service:
                event.source_service = self.service_name
            
            # Get topic and partition key
            topic = event.get_topic_name()
            partition_key = event.get_partition_key()
            
            # Wrap event in envelope
            envelope = IntegrationEventEnvelope.wrap(event)
            
            # Prepare headers
            headers = {
                "event_type": event.event_type,
                "event_id": str(event.event_id),
                "event_version": event.event_version,
                "correlation_id": str(event.correlation_id) if event.correlation_id else "",
                "source_service": event.source_service or "",
            }
            
            # Create outbox message
            outbox_message = OutboxMessage(
                event_id=event.event_id,
                event_type=event.event_type,
                event_version=event.event_version,
                topic=topic,
                partition_key=partition_key,
                payload=envelope.to_json(),
                headers=json.dumps(headers),
                correlation_id=event.correlation_id,
                causation_id=event.causation_id,
                source_service=event.source_service,
                aggregate_id=event.aggregate_id,
            )
            
            outbox_messages.append(outbox_message)
        
        # Save all to outbox
        await self.outbox_repository.add_many(outbox_messages)
        
        if logger:
            logger.info(
                f"Saved {len(events)} integration events to outbox",
                extra={
                    "extra_fields": {
                        "event.count": len(events),
                    }
                },
            )


class OutboxEventPublisherFactory:
    """
    Factory for creating outbox publishers with dependency injection.
    
    This makes it easy to use the outbox publisher with FastAPI
    dependency injection.
    """
    
    def __init__(self, service_name: str):
        """
        Initialize factory.
        
        Args:
            service_name: Name of the service
        """
        self.service_name = service_name
    
    def create(self, session) -> OutboxEventPublisher:
        """
        Create an outbox publisher for a database session.
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            Configured outbox publisher
        """
        repository = OutboxRepository(session)
        return OutboxEventPublisher(repository, self.service_name)
