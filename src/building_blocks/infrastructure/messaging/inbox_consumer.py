"""
Inbox-based integration event consumer with idempotent processing.

This consumer uses the inbox pattern to ensure messages are processed
exactly once, even if they are delivered multiple times by Kafka.
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Type

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

from ...domain.events.integration_event import IntegrationEvent, IntegrationEventEnvelope
from ..persistence.inbox import InboxRepository
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


class InboxIntegrationEventHandler:
    """
    Base class for inbox-based integration event handlers.
    
    Handlers can access the database session to ensure transactional processing.
    """
    
    async def handle(self, event: IntegrationEvent, session: Any) -> None:
        """
        Handle an integration event.
        
        Args:
            event: The integration event to handle
            session: Database session for transactional processing
        """
        raise NotImplementedError


class InboxIntegrationEventConsumer:
    """
    Inbox-based Kafka consumer for integration events.
    
    This consumer uses the inbox pattern to ensure exactly-once processing:
    1. Check if message already exists in inbox (duplicate check)
    2. If duplicate, skip processing
    3. If not duplicate, insert into inbox with status='processing'
    4. Process message with handler
    5. Update inbox status to 'processed'
    6. Commit transaction and Kafka offset
    
    All steps happen in a single database transaction for atomicity.
    
    Example:
        >>> config = KafkaConfig()
        >>> consumer = InboxIntegrationEventConsumer(config, get_session_factory())
        >>> consumer.register_handler(UserCreatedEvent, UserCreatedHandler())
        >>> await consumer.start(["users.created"])
    """
    
    def __init__(
        self,
        kafka_config: KafkaConfig,
        session_factory,
        store_payload: bool = True,
        enable_inbox: Optional[bool] = None,
    ):
        """
        Initialize the inbox consumer.
        
        Args:
            kafka_config: Kafka configuration
            session_factory: Factory function that returns a SQLAlchemy session
            store_payload: Whether to store payload in inbox (for debugging/replay)
            enable_inbox: Override to enable/disable inbox pattern (if None, uses kafka_config.enable_inbox)
        """
        self.kafka_config = kafka_config
        self.session_factory = session_factory
        self.store_payload = store_payload
        # Allow override, otherwise use config
        self.enable_inbox = enable_inbox if enable_inbox is not None else kafka_config.enable_inbox
        
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._started = False
        self._running = False
        self._consume_task: Optional[asyncio.Task] = None
        
        # Handler registry: event_type -> (event_class, handler)
        self._handlers: Dict[str, tuple[Type[IntegrationEvent], InboxIntegrationEventHandler]] = {}
        
        # Topic subscriptions
        self._topics: List[str] = []
    
    def register_handler(
        self,
        event_type: Type[IntegrationEvent],
        handler: InboxIntegrationEventHandler,
    ) -> None:
        """
        Register a handler for an integration event type.
        
        Args:
            event_type: The integration event class
            handler: The handler instance
        """
        event_type_name = event_type.__name__
        self._handlers[event_type_name] = (event_type, handler)
        
        if logger:
            logger.info(
                f"Registered inbox handler for integration event: {event_type_name}",
                extra={
                    "extra_fields": {
                        "event.type": event_type_name,
                        "handler.type": type(handler).__name__,
                    }
                },
            )
    
    async def start(self, topics: List[str]) -> None:
        """
        Start the Kafka consumer and begin consuming messages.
        
        Args:
            topics: List of Kafka topics to subscribe to
        """
        if self._started:
            return
        
        self._topics = topics
        consumer_config = self.kafka_config.get_consumer_config()
        
        # Create consumer with JSON deserializer
        self._consumer = AIOKafkaConsumer(
            *topics,
            **consumer_config,
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            key_deserializer=lambda v: v.decode('utf-8') if v else None,
        )
        
        try:
            await self._consumer.start()
            self._started = True
            self._running = True
            
            if logger:
                logger.info(
                    "Inbox integration event consumer started",
                    extra={
                        "extra_fields": {
                            "kafka.bootstrap_servers": self.kafka_config.bootstrap_servers,
                            "kafka.group_id": self.kafka_config.consumer_group_id,
                            "kafka.topics": topics,
                            "inbox.enabled": self.enable_inbox,
                        }
                    },
                )
            
            # Start consuming in background
            self._consume_task = asyncio.create_task(self._consume_loop())
        
        except Exception as e:
            if logger:
                logger.error(f"Failed to start inbox consumer: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the Kafka consumer and cleanup resources."""
        if not self._started:
            return
        
        self._running = False
        
        # Cancel consume task
        if self._consume_task:
            self._consume_task.cancel()
            try:
                await self._consume_task
            except asyncio.CancelledError:
                pass
        
        # Stop consumer
        if self._consumer:
            try:
                await self._consumer.stop()
                self._started = False
                if logger:
                    logger.info("Inbox integration event consumer stopped")
            except Exception as e:
                logger.error(f"Error stopping Kafka consumer: {e}")
    
    async def _consume_loop(self) -> None:
        """Main consume loop that processes messages."""
        if not self._consumer:
            return
        
        while self._running:
            try:
                # Poll for messages
                async for message in self._consumer:
                    if not self._running:
                        break
                    
                    try:
                        await self._process_message_with_inbox(message)
                        
                        # Commit offset after successful processing
                        await self._consumer.commit()
                    
                    except Exception as e:
                        logger.error(
                            f"Error processing message: {e}",
                            extra={
                                "extra_fields": {
                                    "kafka.topic": message.topic,
                                    "kafka.partition": message.partition,
                                    "kafka.offset": message.offset,
                                    "error": str(e),
                                }
                            },
                        )
                        # Don't commit offset - message will be retried
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in consume loop: {e}")
                # Wait before retrying
                await asyncio.sleep(5)
    
    async def _process_message_with_inbox(self, message: Any) -> None:
        """
        Process a message using the inbox pattern (if enabled).
        
        This ensures exactly-once processing by checking for duplicates
        and storing the message in the inbox table.
        """
        # If inbox is disabled, process directly without database storage
        if not self.enable_inbox:
            await self._process_message_direct(message)
            return
        
        # Create a new session for this message
        async with self.session_factory() as session:
            try:
                # Deserialize envelope
                envelope = IntegrationEventEnvelope(**message.value)
                
                # Get inbox repository
                inbox_repository = InboxRepository(session)
                
                # Check if already processed (duplicate detection)
                is_duplicate = await inbox_repository.is_duplicate(envelope.event_id)
                
                if is_duplicate:
                    if logger:
                        logger.info(
                            f"Skipping duplicate message: {envelope.event_type}",
                            extra={
                                "extra_fields": {
                                    "event.type": envelope.event_type,
                                    "event.id": str(envelope.event_id),
                                    "kafka.topic": message.topic,
                                    "kafka.partition": message.partition,
                                    "kafka.offset": message.offset,
                                    "inbox.duplicate": True,
                                }
                            },
                        )
                    return
                
                # Get handler for event type
                event_type_name = envelope.event_type
                
                if event_type_name not in self._handlers:
                    logger.warning(
                        f"No handler registered for event type: {event_type_name}",
                        extra={
                            "extra_fields": {
                                "event.type": event_type_name,
                                "kafka.topic": message.topic,
                            }
                        },
                    )
                    return
                
                event_class, handler = self._handlers[event_type_name]
                
                # Deserialize event
                event = event_class(**envelope.payload)
                
                # Add to inbox (marks as processing)
                await inbox_repository.add(
                    message_id=envelope.event_id,
                    event_type=envelope.event_type,
                    topic=message.topic,
                    partition=message.partition,
                    offset=message.offset,
                    correlation_id=envelope.correlation_id,
                    handler_name=type(handler).__name__,
                    payload=envelope.to_json() if self.store_payload else None,
                )
                
                # Start tracing span if observability is available
                if OBSERVABILITY_AVAILABLE and get_tracer:
                    tracer = get_tracer(__name__)
                    with tracer.start_as_current_span(f"inbox.consume.{event_type_name}") as span:
                        span.set_attribute("messaging.system", "kafka")
                        span.set_attribute("messaging.source", message.topic)
                        span.set_attribute("messaging.kafka.partition", message.partition)
                        span.set_attribute("messaging.kafka.offset", message.offset)
                        span.set_attribute("event.type", event_type_name)
                        span.set_attribute("event.id", str(event.event_id))
                        span.set_attribute("inbox.enabled", True)
                        
                        # Handle the event (pass session for transactional operations)
                        await handler.handle(event, session)
                else:
                    # Handle without tracing
                    await handler.handle(event, session)
                
                # Mark as processed
                await inbox_repository.mark_as_processed(envelope.event_id)
                
                # Commit transaction
                await session.commit()
                
                if logger:
                    logger.info(
                        f"Processed integration event: {event_type_name}",
                        extra={
                            "extra_fields": {
                                "event.type": event_type_name,
                                "event.id": str(event.event_id),
                                "kafka.topic": message.topic,
                                "kafka.partition": message.partition,
                                "kafka.offset": message.offset,
                                "inbox.processed": True,
                            }
                        },
                    )
            
            except Exception as e:
                await session.rollback()
                
                # Try to mark as failed in inbox
                try:
                    envelope = IntegrationEventEnvelope(**message.value)
                    inbox_repository = InboxRepository(session)
                    await inbox_repository.mark_as_failed(envelope.event_id, str(e))
                    await session.commit()
                except Exception as inner_e:
                    logger.error(f"Failed to mark message as failed in inbox: {inner_e}")
                
                logger.error(f"Error processing message with inbox: {e}")
                raise
    
    async def _process_message_direct(self, message: Any) -> None:
        """
        Process a message directly without inbox pattern.
        
        This is used when inbox is disabled. No duplicate detection or
        database storage occurs.
        """
        try:
            # Deserialize envelope
            envelope = IntegrationEventEnvelope(**message.value)
            
            # Get handler for event type
            event_type_name = envelope.event_type
            
            if event_type_name not in self._handlers:
                logger.warning(
                    f"No handler registered for event type: {event_type_name}",
                    extra={
                        "extra_fields": {
                            "event.type": event_type_name,
                            "kafka.topic": message.topic,
                        }
                    },
                )
                return
            
            event_class, handler = self._handlers[event_type_name]
            
            # Deserialize event from payload
            event = event_class(**envelope.payload)
            
            # Copy metadata from envelope to event
            event.event_id = envelope.event_id
            event.correlation_id = envelope.correlation_id
            event.causation_id = envelope.causation_id
            
            # Create a session for handler (if it needs database access)
            async with self.session_factory() as session:
                # Handle the event
                if OBSERVABILITY_AVAILABLE and get_tracer:
                    tracer = get_tracer(__name__)
                    with tracer.start_as_current_span(f"handle_{event_type_name}") as span:
                        span.set_attribute("event.type", event_type_name)
                        span.set_attribute("event.id", str(event.event_id))
                        span.set_attribute("inbox.enabled", False)
                        
                        await handler.handle(event, session)
                else:
                    await handler.handle(event, session)
                
                # Commit transaction
                await session.commit()
            
            if logger:
                logger.info(
                    f"Processed integration event: {event_type_name}",
                    extra={
                        "extra_fields": {
                            "event.type": event_type_name,
                            "event.id": str(event.event_id),
                            "kafka.topic": message.topic,
                            "kafka.partition": message.partition,
                            "kafka.offset": message.offset,
                            "inbox.used": False,
                        }
                    },
                )
        
        except Exception as e:
            logger.error(f"Error processing message directly: {e}")
            raise
    
    async def __aenter__(self):
        """Context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.stop()
