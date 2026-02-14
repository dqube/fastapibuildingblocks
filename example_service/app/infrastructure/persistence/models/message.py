"""SQLAlchemy model for Message entity."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID

from ....core.database import db_session


class MessageModel(db_session.Base):
    """SQLAlchemy model for messages received from Kafka."""
    
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    message_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    content = Column(String, nullable=False)
    sender = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False)
    metadata = Column(JSON, nullable=True)
    processed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<MessageModel(id={self.id}, message_id={self.message_id}, sender={self.sender})>"
