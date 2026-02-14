"""Integration event handlers for message events."""

import logging
from datetime import datetime

from fastapi_building_blocks.infrastructure.messaging.kafka_consumer import IntegrationEventHandler

from ...domain.events.message_events import MessageSentIntegrationEvent
from ...domain.entities.message import Message
from ...infrastructure.persistence.repositories.message_repository import MessageRepository


# Import observability modules (optional)
try:
    from fastapi_building_blocks.observability.logging import get_logger
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False
    get_logger = None


logger = get_logger(__name__) if OBSERVABILITY_AVAILABLE else logging.getLogger(__name__)


class MessageSentIntegrationEventHandler(IntegrationEventHandler):
    """
    Handler for MessageSentIntegrationEvent.
    
    This handler processes messages received from Kafka and saves them
    to the database for later retrieval.
    """
    
    async def handle(self, event: MessageSentIntegrationEvent) -> None:
        """
        Handle a MessageSentIntegrationEvent received from Kafka.
        
        Args:
            event: The integration event to process
        """
        from ...core.database import db_session
        
        # Get async session for database operations
        async for session in db_session.get_session():
            repository = MessageRepository(session)
            
            logger.info(
                f"📨 Received message from Kafka: {event.message_id}",
                extra={
                    "extra_fields": {
                        "event.type": event.event_type,
                        "event.id": str(event.event_id),
                        "message.id": str(event.message_id),
                        "message.sender": event.sender,
                        "message.content": event.content,
                        "message.timestamp": event.timestamp.isoformat(),
                        "correlation_id": str(event.correlation_id) if event.correlation_id else None,
                    }
                },
            )
            
            # Create message entity
            message = Message(
                message_id=event.message_id,
                content=event.content,
                sender=event.sender,
                timestamp=event.timestamp,
                metadata=event.metadata,
                processed_at=datetime.utcnow(),
            )
            
            # Save message to database
            saved_message = await repository.add(message)
            
            # Explicitly commit the transaction
            await session.commit()
            
            logger.info(
                f"✅ Successfully processed and saved message: {event.message_id}",
                extra={
                    "extra_fields": {
                        "message.id": str(event.message_id),
                        "message.sender": event.sender,
                        "saved_id": str(saved_message.id),
                        "processed_at": datetime.utcnow().isoformat(),
                    }
                },
            )
            
            break  # Exit after first iteration since we only need one session

