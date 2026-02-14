"""Message command handlers."""

from uuid import uuid4
from datetime import datetime

from fastapi_building_blocks.application import CommandHandler
from fastapi_building_blocks.infrastructure.messaging.base import IEventPublisher

from ...domain.events.message_events import MessageSentIntegrationEvent
from ..commands.message_commands import SendMessageCommand
from ..dtos import MessageDTO


class SendMessageCommandHandler(CommandHandler[MessageDTO]):
    """
    Handler for SendMessageCommand.
    
    This handler publishes a MessageSentIntegrationEvent to Kafka,
    demonstrating the integration event pattern.
    """
    
    def __init__(self, event_publisher: IEventPublisher):
        """
        Initialize the handler.
        
        Args:
            event_publisher: Event publisher instance (Kafka producer)
        """
        self.event_publisher = event_publisher
    
    async def handle(self, command: SendMessageCommand) -> MessageDTO:
        """
        Handle the send message command.
        
        Args:
            command: The send message command
            
        Returns:
            Message DTO with published message details
        """
        # Generate message ID and timestamp
        message_id = uuid4()
        timestamp = datetime.utcnow()
        
        # Create integration event
        integration_event = MessageSentIntegrationEvent(
            message_id=message_id,
            content=command.content,
            sender=command.sender,
            timestamp=timestamp,
            metadata=command.metadata,
            source_service="User Management Service",
        )
        
        # Publish to Kafka
        await self.event_publisher.publish(integration_event)
        
        # Return DTO
        return MessageDTO(
            message_id=message_id,
            content=command.content,
            sender=command.sender,
            timestamp=timestamp,
            metadata=command.metadata,
        )
