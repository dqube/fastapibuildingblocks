"""Kafka consumer implementation for integration events."""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Type

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

from ...domain.events.integration_event import IntegrationEvent, IntegrationEventEnvelope
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


class IntegrationEventHandler:
    """
    Base class for integration event handlers.
    
    Handlers process integration events received from Kafka.
    Similar to Wolverine's message handlers in .NET.
    """
    
    async def handle(self, event: IntegrationEvent) -> None:
        """
        Handle an integration event.
        
        Args:
            event: The integration event to handle
        """
        raise NotImplementedError


class KafkaIntegrationEventConsumer:
    """
    Kafka consumer for integration events.
    
    This consumer subscribes to Kafka topics and processes integration events,
    similar to Wolverine's message consumption in .NET. It supports:
    - Asynchronous message consumption
    - Automatic event deserialization
    - Handler registration and routing
    - Manual offset commit for reliability
    - Retry logic and error handling
    - OpenTelemetry tracing and metrics
    - Dead letter queue for failed messages
    
    Example:
        >>> config = KafkaConfig()
        >>> consumer = KafkaIntegrationEventConsumer(config)
        >>> consumer.register_handler(UserCreatedIntegrationEvent, UserCreatedHandler())
        >>> await consumer.start(["integration-events.user_created"])
    """
    
    def __init__(self, config: KafkaConfig):
        """
        Initialize the Kafka consumer.
        
        Args:
            config: Kafka configuration
        """
        self.config = config
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._started = False
        self._running = False
        self._consume_task: Optional[asyncio.Task] = None
        
        # Handler registry: event_type -> (event_class, handler)
        self._handlers: Dict[str, tuple[Type[IntegrationEvent], IntegrationEventHandler]] = {}
        
        # Topic subscriptions
        self._topics: List[str] = []
    
    def register_handler(
        self,
        event_type: Type[IntegrationEvent],
        handler: IntegrationEventHandler,
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
                f"Registered handler for integration event: {event_type_name}",
                extra={
                    "extra_fields": {
                        "event.type": event_type_name,
                        "handler.type": type(handler).__name__,
                    }
                },
            )
    
    def register_handler_function(
        self,
        event_type: Type[IntegrationEvent],
        handler_func: Callable[[IntegrationEvent], Any],
    ) -> None:
        """
        Register a handler function for an integration event type.
        
        Args:
            event_type: The integration event class
            handler_func: The handler function (can be sync or async)
        """
        # Wrap function in a handler class
        class FunctionHandler(IntegrationEventHandler):
            def __init__(self, func):
                self.func = func
            
            async def handle(self, event: IntegrationEvent) -> None:
                if asyncio.iscoroutinefunction(self.func):
                    await self.func(event)
                else:
                    self.func(event)
        
        self.register_handler(event_type, FunctionHandler(handler_func))
    
    async def start(self, topics: List[str]) -> None:
        """
        Start the Kafka consumer and begin consuming messages.
        
        Args:
            topics: List of Kafka topics to subscribe to
        """
        if self._started:
            return
        
        self._topics = topics
        consumer_config = self.config.get_consumer_config()
        
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
                    "Kafka integration event consumer started",
                    extra={
                        "extra_fields": {
                            "kafka.bootstrap_servers": self.config.bootstrap_servers,
                            "kafka.group_id": self.config.consumer_group_id,
                            "kafka.topics": topics,
                        }
                    },
                )
            
            # Start consuming in background
            self._consume_task = asyncio.create_task(self._consume_loop())
        
        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
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
                    logger.info("Kafka integration event consumer stopped")
            except Exception as e:
                logger.error(f"Error stopping Kafka consumer: {e}")
    
    async def _consume_loop(self) -> None:
        """Main consume loop that processes messages."""
        if not self._consumer:
            return
        
        retry_counts: Dict[tuple[str, int, int], int] = {}  # (topic, partition, offset) -> retry_count
        
        while self._running:
            try:
                # Poll for messages
                async for message in self._consumer:
                    if not self._running:
                        break
                    
                    # Track retry count
                    message_key = (message.topic, message.partition, message.offset)
                    retry_count = retry_counts.get(message_key, 0)
                    
                    try:
                        await self._process_message(message)
                        
                        # Commit offset after successful processing
                        await self._consumer.commit()
                        
                        # Remove from retry tracking
                        retry_counts.pop(message_key, None)
                    
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
                        
                        # Increment retry count
                        retry_count += 1
                        retry_counts[message_key] = retry_count
                        
                        # Check if max retries exceeded
                        if retry_count >= self.config.max_retry_attempts:
                            if self.config.enable_dlq:
                                await self._send_to_dlq(message, e)
                            
                            # Commit offset to skip this message
                            await self._consumer.commit()
                            retry_counts.pop(message_key, None)
                        else:
                            # Don't commit offset, will retry on next poll
                            logger.info(f"Will retry message, attempt {retry_count}/{self.config.max_retry_attempts}")
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in consume loop: {e}")
                # Wait before retrying
                await asyncio.sleep(5)
    
    async def _process_message(self, message: Any) -> None:
        """Process a single Kafka message."""
        try:
            # Deserialize envelope
            envelope = IntegrationEventEnvelope(**message.value)
            
            # Get headers as dict
            headers = {k: v.decode('utf-8') if isinstance(v, bytes) else v 
                      for k, v in message.headers}
            
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
            
            # Start tracing span if observability is available
            if OBSERVABILITY_AVAILABLE and get_tracer:
                tracer = get_tracer(__name__)
                with tracer.start_as_current_span(f"kafka.consume.{event_type_name}") as span:
                    span.set_attribute("messaging.system", "kafka")
                    span.set_attribute("messaging.source", message.topic)
                    span.set_attribute("messaging.kafka.partition", message.partition)
                    span.set_attribute("messaging.kafka.offset", message.offset)
                    span.set_attribute("event.type", event_type_name)
                    span.set_attribute("event.id", str(event.event_id))
                    
                    # Handle the event
                    await handler.handle(event)
            else:
                # Handle without tracing
                await handler.handle(event)
            
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
                        }
                    },
                )
        
        except Exception as e:
            logger.error(f"Error deserializing or handling message: {e}")
            raise
    
    async def _send_to_dlq(self, message: Any, error: Exception) -> None:
        """Send failed message to dead letter queue."""
        # This would require a producer instance - for now just log
        dlq_topic = f"{message.topic}{self.config.dlq_topic_suffix}"
        
        logger.error(
            f"Max retries exceeded, message should be sent to DLQ: {dlq_topic}",
            extra={
                "extra_fields": {
                    "kafka.dlq_topic": dlq_topic,
                    "kafka.original_topic": message.topic,
                    "kafka.partition": message.partition,
                    "kafka.offset": message.offset,
                    "error": str(error),
                }
            },
        )
    
    async def __aenter__(self):
        """Context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.stop()
