"""Message entity for storing received messages."""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from dataclasses import dataclass, field


@dataclass
class Message:
    """
    Message entity representing a received message from Kafka.
    
    This entity tracks messages that have been received and processed
    through the Kafka integration event system.
    """
    
    content: str
    sender: str
    message_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    processed_at: datetime = field(default_factory=datetime.utcnow)
    id: Optional[UUID] = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<Message(id={self.id}, message_id={self.message_id}, sender={self.sender})>"
