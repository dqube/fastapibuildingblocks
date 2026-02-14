"""
Outbox relay worker for publishing events from outbox to Kafka.

This background worker polls the outbox table and publishes pending
messages to Kafka, ensuring reliable event delivery.
"""

import asyncio
import json
import logging
from typing import Optional

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

from ..persistence.outbox import OutboxRepository, OutboxMessage
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


class OutboxRelay:
    """
    Outbox relay worker that publishes messages from outbox to Kafka.
    
    This worker runs as a background process, continuously polling the outbox
    table for pending messages and publishing them to Kafka.
    
    Features:
    - Polling with configurable interval
    - Batch processing for efficiency
    - Automatic retry with exponential backoff
    - Dead letter queue for permanently failed messages
    - Graceful shutdown
    - Multiple worker support with pessimistic locking
    
    Example:
        >>> relay = OutboxRelay(config, get_session_factory())
        >>> await relay.start()
        >>> # Relay runs in background
        >>> await relay.stop()
    """
    
    def __init__(
        self,
        kafka_config: KafkaConfig,
        session_factory,
        poll_interval_seconds: int = 5,
        batch_size: int = 100,
        max_attempts: int = 3,
    ):
        """
        Initialize the outbox relay.
        
        Args:
            kafka_config: Kafka configuration
            session_factory: Factory function that returns a SQLAlchemy session
            poll_interval_seconds: How often to poll for messages
            batch_size: Maximum messages to process per batch
            max_attempts: Maximum retry attempts before marking as failed
        """
        self.kafka_config = kafka_config
        self.session_factory = session_factory
        self.poll_interval_seconds = poll_interval_seconds
        self.batch_size = batch_size
        self.max_attempts = max_attempts
        
        self._producer: Optional[AIOKafkaProducer] = None
        self._running = False
        self._relay_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start the outbox relay worker."""
        if self._running:
            return
        
        # Create Kafka producer
        producer_config = self.kafka_config.get_producer_config()
        self._producer = AIOKafkaProducer(
            **producer_config,
            value_serializer=lambda v: v.encode('utf-8') if isinstance(v, str) else v,
            key_serializer=lambda v: v.encode('utf-8') if v else None,
        )
        
        try:
            await self._producer.start()
            self._running = True
            
            if logger:
                logger.info(
                    "Outbox relay started",
                    extra={
                        "extra_fields": {
                            "kafka.bootstrap_servers": self.kafka_config.bootstrap_servers,
                            "outbox.poll_interval": self.poll_interval_seconds,
                            "outbox.batch_size": self.batch_size,
                        }
                    },
                )
            
            # Start relay loop
            self._relay_task = asyncio.create_task(self._relay_loop())
        
        except Exception as e:
            logger.error(f"Failed to start outbox relay: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the outbox relay worker gracefully."""
        if not self._running:
            return
        
        self._running = False
        
        # Cancel relay task
        if self._relay_task:
            self._relay_task.cancel()
            try:
                await self._relay_task
            except asyncio.CancelledError:
                pass
        
        # Stop producer
        if self._producer:
            try:
                await self._producer.stop()
                if logger:
                    logger.info("Outbox relay stopped")
            except Exception as e:
                logger.error(f"Error stopping Kafka producer: {e}")
    
    async def _relay_loop(self) -> None:
        """Main relay loop that polls and publishes messages."""
        while self._running:
            try:
                # Process a batch of messages
                await self._process_batch()
                
                # Wait before next poll
                await asyncio.sleep(self.poll_interval_seconds)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in relay loop: {e}")
                # Wait before retrying
                await asyncio.sleep(self.poll_interval_seconds)
    
    async def _process_batch(self) -> None:
        """Process a batch of pending messages."""
        # Create a new session for this batch
        async with self.session_factory() as session:
            try:
                # Get repository
                repository = OutboxRepository(session)
                
                # Get pending messages (with locking)
                messages = await repository.get_pending_messages(
                    limit=self.batch_size,
                    lock_duration_seconds=300  # Lock for 5 minutes
                )
                
                if not messages:
                    return
                
                if logger:
                    logger.debug(f"Processing {len(messages)} outbox messages")
                
                # Publish each message
                for message in messages:
                    try:
                        await self._publish_message(message)
                        await repository.mark_as_published(message.id)
                    except Exception as e:
                        error_msg = str(e)
                        logger.error(
                            f"Failed to publish outbox message: {message.id}",
                            extra={
                                "extra_fields": {
                                    "outbox.message_id": str(message.id),
                                    "outbox.event_type": message.event_type,
                                    "error": error_msg,
                                }
                            },
                        )
                        await repository.mark_as_failed(
                            message.id,
                            error_msg,
                            self.max_attempts
                        )
                
                # Commit changes
                await session.commit()
                
                if logger:
                    logger.info(
                        f"Published {len(messages)} outbox messages",
                        extra={
                            "extra_fields": {
                                "outbox.batch_size": len(messages),
                            }
                        },
                    )
            
            except Exception as e:
                await session.rollback()
                logger.error(f"Error processing outbox batch: {e}")
    
    async def _publish_message(self, message: OutboxMessage) -> None:
        """
        Publish a single outbox message to Kafka.
        
        Args:
            message: Outbox message to publish
        """
        # Parse headers
        headers_dict = json.loads(message.headers) if message.headers else {}
        headers = [(k, v.encode('utf-8') if isinstance(v, str) else v) 
                   for k, v in headers_dict.items()]
        
        # Start tracing span if observability is available
        if OBSERVABILITY_AVAILABLE and get_tracer:
            tracer = get_tracer(__name__)
            with tracer.start_as_current_span(f"outbox.relay.{message.event_type}") as span:
                span.set_attribute("messaging.system", "kafka")
                span.set_attribute("messaging.destination", message.topic)
                span.set_attribute("messaging.destination_kind", "topic")
                span.set_attribute("messaging.kafka.partition_key", message.partition_key or "")
                span.set_attribute("event.type", message.event_type)
                span.set_attribute("event.id", str(message.event_id))
                span.set_attribute("outbox.message_id", str(message.id))
                
                await self._send_to_kafka(message, headers)
        else:
            await self._send_to_kafka(message, headers)
    
    async def _send_to_kafka(self, message: OutboxMessage, headers: list) -> None:
        """Internal method to send message to Kafka."""
        try:
            # Send to Kafka
            record_metadata = await self._producer.send_and_wait(
                topic=message.topic,
                value=message.payload,  # Already JSON serialized
                key=message.partition_key,
                headers=headers,
            )
            
            if logger:
                logger.debug(
                    f"Published to Kafka: {message.event_type}",
                    extra={
                        "extra_fields": {
                            "event.type": message.event_type,
                            "event.id": str(message.event_id),
                            "kafka.topic": message.topic,
                            "kafka.partition": record_metadata.partition,
                            "kafka.offset": record_metadata.offset,
                            "outbox.message_id": str(message.id),
                        }
                    },
                )
        
        except KafkaError as e:
            logger.error(
                f"Kafka error publishing message: {message.event_type}",
                extra={
                    "extra_fields": {
                        "event.type": message.event_type,
                        "event.id": str(message.event_id),
                        "kafka.topic": message.topic,
                        "outbox.message_id": str(message.id),
                        "error": str(e),
                    }
                },
            )
            raise
    
    async def __aenter__(self):
        """Context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.stop()
