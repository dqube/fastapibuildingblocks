"""Message-related commands."""

from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi_building_blocks.application import Command


class SendMessageCommand(Command):
    """
    Command to send a message to Kafka.
    
    This command will trigger the publication of a MessageSentIntegrationEvent
    to Kafka, which can be consumed by other services or our own service.
    """
    
    content: str
    sender: str
    metadata: Optional[dict] = None
