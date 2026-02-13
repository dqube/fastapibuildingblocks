"""Kafka producer implementation for integration events."""

import json
import logging
from typing import List, Optional
from uuid import uuid4

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

from ...domain.events.integration_event import IntegrationEvent, IntegrationEventEnvelope
from .base import IEventPublisher
from .kafka_config import KafkaConfig


# Import observability modules (optional)
try:
    from ...observability.tracing import get_tracer
    from ...observability.logging import get_logger
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False
    get_tracer = None
    get_logger = None


logger = get_logger(__name__) if OBSERVABILITY_AVAILABLE else logging.getLogger(__name__)


class KafkaIntegrationEventPublisher(IEventPublisher):
    """
    Kafka implementation of integration event publisher.
    
    This publisher sends integration events to Kafka topics, similar to Wolverine's
    integration event publishing in .NET. It supports:
    - Asynchronous message publishing
    - Automatic topic routing based on event type
    - Message partitioning for ordering guarantees
    - Retry logic and error handling
    - OpenTelemetry tracing and metrics
    - Dead letter queue for failed messages
    
    Example:
        >>> config = KafkaConfig()
        >>> publisher = KafkaIntegrationEventPublisher(config)
        >>> await publisher.start()
        >>> await publisher.publish(UserCreatedIntegrationEvent(...))
        >>> await publisher.stop()
    """
    
    def __init__(self, config: KafkaConfig):
        """
        Initialize the Kafka publisher.
        
        Args:
            config: Kafka configuration
        """
        self.config = config
        self._producer: Optional[AIOKafkaProducer] = None
        self._started = False
    
    async def start(self) -> None:
        """
        Start the Kafka producer.
        
        This must be called before publishing events.
        """
        if self._started:
            return
        
        producer_config = self.config.get_producer_config()
        
        # Create producer with JSON serializer
        self._producer = AIOKafkaProducer(
            **producer_config,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda v: v.encode('utf-8') if v else None,
        )
        
        try:
            await self._producer.start()
            self._started = True
            if logger:
                logger.info(
                    "Kafka integration event publisher started",
                    extra={
                        "extra_fields": {
                            "kafka.bootstrap_servers": self.config.bootstrap_servers,
                            "kafka.service_name": self.config.service_name,
                        }
                    },
                )
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the Kafka producer and cleanup resources."""
        if not self._started or not self._producer:
            return
        
        try:
            await self._producer.stop()
            self._started = False
            if logger:
                logger.info("Kafka integration event publisher stopped")
        except Exception as e:
            logger.error(f"Error stopping Kafka producer: {e}")
    
    async def publish(self, event: IntegrationEvent) -> None:
        """
        Publish a single integration event to Kafka.
        
        Args:
            event: The integration event to publish
            
        Raises:
            RuntimeError: If producer is not started
            KafkaError: If publishing fails
        """
        if not self._started or not self._producer:
            raise RuntimeError(
                "Kafka producer not started. Call start() before publishing events."
            )
        
        # Set source service if not already set
        if not event.source_service:
            event.source_service = self.config.service_name
        
        # Get topic and partition key
        topic = event.get_topic_name()
        partition_key = event.get_partition_key()
        
        # Wrap event in envelope
        envelope = IntegrationEventEnvelope.wrap(event)
        
        # Start tracing span if observability is available
        if OBSERVABILITY_AVAILABLE and get_tracer:
            tracer = get_tracer(__name__)
            with tracer.start_as_current_span(f"kafka.publish.{event.event_type}") as span:
                span.set_attribute("messaging.system", "kafka")
                span.set_attribute("messaging.destination", topic)
                span.set_attribute("messaging.destination_kind", "topic")
                span.set_attribute("messaging.kafka.partition_key", partition_key or "")
                span.set_attribute("event.type", event.event_type)
                span.set_attribute("event.id", str(event.event_id))
                
                await self._send_to_kafka(topic, partition_key, envelope, event)
        else:
            await self._send_to_kafka(topic, partition_key, envelope, event)
    
    async def _send_to_kafka(
        self,
        topic: str,
        partition_key: Optional[str],
        envelope: IntegrationEventEnvelope,
        event: IntegrationEvent,
    ) -> None:
        """Internal method to send message to Kafka."""
        try:
            # Convert envelope to dict for serialization
            message_value = envelope.model_dump(mode='json')
            
            # Send to Kafka
            record_metadata = await self._producer.send_and_wait(
                topic=topic,
                value=message_value,
                key=partition_key,
                headers=[
                    ("event_type", event.event_type.encode('utf-8')),
                    ("event_id", str(event.event_id).encode('utf-8')),
                    ("event_version", event.event_version.encode('utf-8')),
                    ("correlation_id", str(event.correlation_id).encode('utf-8') if event.correlation_id else b""),
                    ("source_service", (event.source_service or "").encode('utf-8')),
                ],
            )
            
            if logger:
                logger.info(
                    f"Published integration event: {event.event_type}",
                    extra={
                        "extra_fields": {
                            "event.type": event.event_type,
                            "event.id": str(event.event_id),
                            "kafka.topic": topic,
                            "kafka.partition": record_metadata.partition,
                            "kafka.offset": record_metadata.offset,
                        }
                    },
                )
        
        except KafkaError as e:
            logger.error(
                f"Failed to publish integration event: {event.event_type}",
                extra={
                    "extra_fields": {
                        "event.type": event.event_type,
                        "event.id": str(event.event_id),
                        "kafka.topic": topic,
                        "error": str(e),
                    }
                },
            )
            
            # If DLQ is enabled, try to send to DLQ
            if self.config.enable_dlq:
                await self._send_to_dlq(topic, partition_key, envelope, e)
            
            raise
    
    async def _send_to_dlq(
        self,
        original_topic: str,
        partition_key: Optional[str],
        envelope: IntegrationEventEnvelope,
        error: Exception,
    ) -> None:
        """Send failed message to dead letter queue."""
        dlq_topic = f"{original_topic}{self.config.dlq_topic_suffix}"
        
        try:
            # Add error information to envelope
            dlq_envelope = envelope.model_dump(mode='json')
            dlq_envelope['dlq_metadata'] = {
                'original_topic': original_topic,
                'error_message': str(error),
                'error_type': type(error).__name__,
            }
            
            await self._producer.send_and_wait(
                topic=dlq_topic,
                value=dlq_envelope,
                key=partition_key,
            )
            
            if logger:
                logger.warning(
                    f"Sent message to DLQ: {dlq_topic}",
                    extra={
                        "extra_fields": {
                            "kafka.dlq_topic": dlq_topic,
                            "kafka.original_topic": original_topic,
                            "event.id": str(envelope.event_id),
                        }
                    },
                )
        except Exception as dlq_error:
            logger.error(f"Failed to send message to DLQ: {dlq_error}")
    
    async def publish_many(self, events: List[IntegrationEvent]) -> None:
        """
        Publish multiple integration events to Kafka.
        
        This method sends events in batch for better performance.
        
        Args:
            events: List of integration events to publish
            
        Raises:
            RuntimeError: If producer is not started
        """
        if not self._started or not self._producer:
            raise RuntimeError(
                "Kafka producer not started. Call start() before publishing events."
            )
        
        if not events:
            return
        
        # Publish all events (batching is handled by aiokafka internally)
        for event in events:
            await self.publish(event)
        
        # Flush to ensure all messages are sent
        await self._producer.flush()
        
        if logger:
            logger.info(
                f"Published {len(events)} integration events",
                extra={
                    "extra_fields": {
                        "event.count": len(events),
                    }
                },
            )
    
    async def __aenter__(self):
        """Context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.stop()
