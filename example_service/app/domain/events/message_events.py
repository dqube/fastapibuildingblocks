"""Message-related integration events."""

from typing import Optional
from uuid import UUID
from datetime import datetime

from building_blocks.domain.events.integration_event import IntegrationEvent


class MessageSentIntegrationEvent(IntegrationEvent):
    """
    Integration event raised when a message is sent to Kafka.
    
    This event will be published to Kafka and can be consumed by other services
    or by our own service to demonstrate the full integration event pattern.
    """
    
    message_id: UUID
    content: str
    sender: str
    timestamp: datetime
    metadata: Optional[dict] = None
    
    def get_topic_name(self) -> str:
        """Override to specify custom topic name."""
        return "integration-events.message_sent"
    
    def get_partition_key(self) -> Optional[str]:
        """Use sender as partition key to ensure messages from same sender are ordered."""
        return self.sender


class MessageReceivedIntegrationEvent(IntegrationEvent):
    """
    Integration event raised when a message is received from Kafka.
    
    This is just for demonstration - in a real system, this would be a different
    event type that gets triggered when we process incoming messages.
    """
    
    message_id: UUID
    content: str
    sender: str
    received_at: datetime
    processed_by: str
    
    def get_topic_name(self) -> str:
        """Override to specify custom topic name."""
        return "integration-events.message_received"
