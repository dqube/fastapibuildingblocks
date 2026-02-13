"""
Factory for creating event publishers based on configuration.

This factory returns the appropriate publisher implementation based on
whether the outbox pattern is enabled or not.
"""

import logging
from typing import Optional

from .base import IEventPublisher
from .kafka_config import KafkaConfig
from .kafka_producer import KafkaIntegrationEventPublisher
from .outbox_publisher import OutboxEventPublisher
from ..persistence.outbox import OutboxRepository


# Import observability modules (optional)
try:
    from ...observability.logging import get_logger
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False
    get_logger = None


logger = get_logger(__name__) if OBSERVABILITY_AVAILABLE else logging.getLogger(__name__)


class IntegrationEventPublisherFactory:
    """
    Factory for creating integration event publishers.
    
    Returns the appropriate publisher based on configuration:
    - If outbox is enabled: Returns OutboxEventPublisher (stores in database)
    - If outbox is disabled: Returns KafkaIntegrationEventPublisher (publishes directly)
    
    Example:
        >>> config = KafkaConfig(enable_outbox=True)
        >>> factory = IntegrationEventPublisherFactory(config)
        >>> 
        >>> # Create outbox publisher (requires session)
        >>> async with session:
        >>>     publisher = factory.create_publisher(session=session)
        >>>     await publisher.publish(event)
        >>> 
        >>> # Create direct publisher (no session needed)
        >>> config = KafkaConfig(enable_outbox=False)
        >>> factory = IntegrationEventPublisherFactory(config)
        >>> async with factory.create_publisher() as publisher:
        >>>     await publisher.publish(event)
    """
    
    def __init__(self, kafka_config: KafkaConfig):
        """
        Initialize the factory.
        
        Args:
            kafka_config: Kafka configuration
        """
        self.kafka_config = kafka_config
        self._direct_publisher: Optional[KafkaIntegrationEventPublisher] = None
    
    def create_publisher(
        self,
        session: Optional[any] = None,
        service_name: Optional[str] = None,
    ) -> IEventPublisher:
        """
        Create an event publisher based on configuration.
        
        Args:
            session: Database session (required if outbox is enabled)
            service_name: Service name for metadata (defaults to config.service_name)
            
        Returns:
            Event publisher instance
            
        Raises:
            ValueError: If outbox is enabled but session is not provided
        """
        service_name = service_name or self.kafka_config.service_name
        
        if self.kafka_config.enable_outbox:
            # Outbox pattern - requires session
            if session is None:
                raise ValueError(
                    "Database session is required when outbox pattern is enabled. "
                    "Either provide a session or disable outbox with enable_outbox=False"
                )
            
            outbox_repository = OutboxRepository(session)
            publisher = OutboxEventPublisher(
                outbox_repository=outbox_repository,
                service_name=service_name,
                store_payload=True,
            )
            
            if logger:
                logger.info(
                    "Created outbox event publisher",
                    extra={
                        "extra_fields": {
                            "publisher.type": "outbox",
                            "service_name": service_name,
                            "outbox.enabled": True,
                        }
                    },
                )
            
            return publisher
        
        else:
            # Direct publishing - no session needed
            # Reuse the same publisher instance
            if self._direct_publisher is None:
                self._direct_publisher = KafkaIntegrationEventPublisher(
                    kafka_config=self.kafka_config,
                    service_name=service_name,
                )
            
            if logger:
                logger.info(
                    "Using direct Kafka event publisher",
                    extra={
                        "extra_fields": {
                            "publisher.type": "direct",
                            "service_name": service_name,
                            "outbox.enabled": False,
                        }
                    },
                )
            
            return self._direct_publisher
    
    async def cleanup(self) -> None:
        """Cleanup resources (close direct publisher if created)."""
        if self._direct_publisher is not None:
            await self._direct_publisher.close()
            self._direct_publisher = None


def create_event_publisher(
    kafka_config: KafkaConfig,
    session: Optional[any] = None,
    service_name: Optional[str] = None,
) -> IEventPublisher:
    """
    Convenience function to create an event publisher.
    
    Args:
        kafka_config: Kafka configuration
        session: Database session (required if outbox is enabled)
        service_name: Service name for metadata
        
    Returns:
        Event publisher instance
        
    Example:
        >>> # With outbox (requires session)
        >>> config = KafkaConfig(enable_outbox=True)
        >>> async with get_session() as session:
        >>>     publisher = create_event_publisher(config, session=session)
        >>>     await publisher.publish(event)
        >>> 
        >>> # Without outbox (direct publishing)
        >>> config = KafkaConfig(enable_outbox=False)
        >>> publisher = create_event_publisher(config)
        >>> async with publisher:
        >>>     await publisher.publish(event)
    """
    factory = IntegrationEventPublisherFactory(kafka_config)
    return factory.create_publisher(session=session, service_name=service_name)
