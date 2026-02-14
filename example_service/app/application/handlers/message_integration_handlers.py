"""Integration event handlers for message events."""

import logging
from datetime import datetime

from building_blocks.infrastructure.messaging import InboxIntegrationEventHandler

from ...domain.events.message_events import MessageSentIntegrationEvent
from ...domain.entities.message import Message
from ...infrastructure.persistence.repositories.message_repository import MessageRepository


# Import observability modules (optional)
try:
    from building_blocks.observability.logging import get_logger
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False
    get_logger = None


logger = get_logger(__name__) if OBSERVABILITY_AVAILABLE else logging.getLogger(__name__)


class MessageSentIntegrationEventHandler(InboxIntegrationEventHandler):
    """
    Handler for MessageSentIntegrationEvent.
    
    This handler processes messages received from Kafka and saves them
    to the database for later retrieval. Uses inbox pattern for exactly-once processing.
    """
    
    async def handle(self, event: MessageSentIntegrationEvent, session) -> None:
        """
        Handle a MessageSentIntegrationEvent received from Kafka.
        
        Args:
            event: The integration event to process
            session: Database session (provided by inbox consumer for transactional processing)
        """
        # Use provided session (part of inbox transaction)
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
        
        # Save message to database (uses session from inbox transaction)
        saved_message = await repository.add(message)
        
        # No need to commit here - inbox consumer will commit the transaction
        # (which includes both the inbox entry and this message)
        
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
