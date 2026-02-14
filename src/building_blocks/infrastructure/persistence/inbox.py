"""
Inbox pattern implementation for idempotent message processing.

The inbox pattern ensures that messages are processed exactly once by storing
message IDs in a database table. This prevents duplicate processing even if
messages are delivered multiple times by Kafka.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import Column, String, DateTime, Text, Index, Boolean, select, delete
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class InboxStatus(str, Enum):
    """Status of an inbox message."""
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class InboxMessage(Base):
    """
    Inbox table for tracking processed messages.
    
    This ensures idempotent message processing by storing message IDs
    and checking for duplicates before processing.
    
    Workflow:
    1. Message arrives from Kafka
    2. Check if message_id exists in inbox
    3. If exists, skip processing (duplicate)
    4. If not exists, insert with status='processing'
    5. Process message
    6. Update status to 'processed'
    """
    
    __tablename__ = "inbox_messages"
    
    # Primary key (use message ID as primary key for uniqueness)
    message_id = Column(PG_UUID(as_uuid=True), primary_key=True)
    
    # Event metadata
    event_type = Column(String(255), nullable=False, index=True)
    event_version = Column(String(50), nullable=False, default="1.0")
    
    # Routing information
    topic = Column(String(255), nullable=False, index=True)
    partition = Column(String(50), nullable=False)
    offset = Column(String(50), nullable=False)
    
    # Correlation tracking
    correlation_id = Column(PG_UUID(as_uuid=True), nullable=True, index=True)
    
    # Processing metadata
    status = Column(String(50), nullable=False, default=InboxStatus.PROCESSING, index=True)
    received_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    processed_at = Column(DateTime, nullable=True)
    locked_until = Column(DateTime, nullable=True, index=True)
    
    # Retry tracking
    attempt_count = Column(String(50), nullable=False, default="0")
    last_error = Column(Text, nullable=True)
    
    # Handler information
    handler_name = Column(String(255), nullable=True)
    
    # Payload (optional, for debugging/replay)
    payload = Column(Text, nullable=True)
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('ix_inbox_status_received', 'status', 'received_at'),
        Index('ix_inbox_topic_partition_offset', 'topic', 'partition', 'offset'),
    )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'message_id': str(self.message_id),
            'event_type': self.event_type,
            'event_version': self.event_version,
            'topic': self.topic,
            'partition': self.partition,
            'offset': self.offset,
            'correlation_id': str(self.correlation_id) if self.correlation_id else None,
            'status': self.status,
            'received_at': self.received_at.isoformat() if self.received_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'attempt_count': self.attempt_count,
            'last_error': self.last_error,
            'handler_name': self.handler_name,
        }


class InboxRepository:
    """Repository for managing inbox messages."""
    
    def __init__(self, session):
        """
        Initialize repository.
        
        Args:
            session: SQLAlchemy session
        """
        self.session = session
    
    async def is_duplicate(self, message_id: UUID) -> bool:
        """
        Check if a message has already been processed.
        
        Args:
            message_id: Message ID to check
            
        Returns:
            True if message already exists, False otherwise
        """
        stmt = select(InboxMessage).where(InboxMessage.message_id == message_id)
        result = await self.session.execute(stmt)
        exists = result.scalar_one_or_none()
        return exists is not None
    
    async def add(
        self,
        message_id: UUID,
        event_type: str,
        topic: str,
        partition: int,
        offset: int,
        correlation_id: Optional[UUID] = None,
        handler_name: Optional[str] = None,
        payload: Optional[str] = None,
    ) -> InboxMessage:
        """
        Add a message to the inbox.
        
        This should be called in the same transaction as message processing
        to ensure atomicity.
        
        Args:
            message_id: Unique message ID
            event_type: Type of the event
            topic: Kafka topic
            partition: Kafka partition
            offset: Kafka offset
            correlation_id: Optional correlation ID
            handler_name: Name of the handler processing this message
            payload: Optional payload for debugging/replay
            
        Returns:
            Created inbox message
        """
        message = InboxMessage(
            message_id=message_id,
            event_type=event_type,
            topic=topic,
            partition=str(partition),
            offset=str(offset),
            correlation_id=correlation_id,
            status=InboxStatus.PROCESSING,
            handler_name=handler_name,
            payload=payload,
        )
        
        self.session.add(message)
        return message
    
    async def mark_as_processed(self, message_id: UUID) -> None:
        """
        Mark a message as successfully processed.
        
        Args:
            message_id: ID of the message
        """
        stmt = select(InboxMessage).where(InboxMessage.message_id == message_id)
        result = await self.session.execute(stmt)
        message = result.scalar_one_or_none()
        if message:
            message.status = InboxStatus.PROCESSED
            message.processed_at = datetime.utcnow()
    
    async def mark_as_failed(
        self,
        message_id: UUID,
        error: str
    ) -> None:
        """
        Mark a message as failed.
        
        Args:
            message_id: ID of the message
            error: Error message
        """
        stmt = select(InboxMessage).where(InboxMessage.message_id == message_id)
        result = await self.session.execute(stmt)
        message = result.scalar_one_or_none()
        if message:
            message.attempt_count = str(int(message.attempt_count) + 1)
            message.last_error = error
            message.status = InboxStatus.FAILED
            message.locked_until = None
    
    async def get_stuck_messages(
        self,
        timeout_minutes: int = 30,
        limit: int = 100
    ) -> List[InboxMessage]:
        """
        Get messages that are stuck in processing state.
        
        These might be from crashed workers and need to be retried.
        
        Args:
            timeout_minutes: Messages in processing state longer than this are considered stuck
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of stuck messages
        """
        cutoff = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        
        stmt = (
            select(InboxMessage)
            .where(
                InboxMessage.status == InboxStatus.PROCESSING,
                InboxMessage.received_at < cutoff
            )
            .order_by(InboxMessage.received_at)
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def cleanup_old_messages(self, days: int = 30) -> int:
        """
        Clean up old processed messages.
        
        Args:
            days: Delete messages older than this many days
            
        Returns:
            Number of messages deleted
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        stmt = (
            delete(InboxMessage)
            .where(
                InboxMessage.status == InboxStatus.PROCESSED,
                InboxMessage.processed_at < cutoff
            )
        )
        
        result = await self.session.execute(stmt)
        return result.rowcount
    
    async def get_failed_messages(self, limit: int = 100) -> List[InboxMessage]:
        """
        Get failed messages for inspection.
        
        Args:
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of failed messages
        """
        stmt = (
            select(InboxMessage)
            .where(InboxMessage.status == InboxStatus.FAILED)
            .order_by(InboxMessage.received_at.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def retry_failed_message(self, message_id: UUID) -> None:
        """
        Reset a failed message to processing for retry.
        
        Args:
            message_id: ID of the message
        """
        stmt = select(InboxMessage).where(InboxMessage.message_id == message_id)
        result = await self.session.execute(stmt)
        message = result.scalar_one_or_none()
        if message:
            message.status = InboxStatus.PROCESSING
            message.locked_until = None
            message.last_error = None


# SQL for creating the table (PostgreSQL)
CREATE_INBOX_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS inbox_messages (
    message_id UUID PRIMARY KEY,
    event_type VARCHAR(255) NOT NULL,
    event_version VARCHAR(50) NOT NULL DEFAULT '1.0',
    topic VARCHAR(255) NOT NULL,
    partition VARCHAR(50) NOT NULL,
    offset VARCHAR(50) NOT NULL,
    correlation_id UUID,
    status VARCHAR(50) NOT NULL DEFAULT 'processing',
    received_at TIMESTAMP NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMP,
    locked_until TIMESTAMP,
    attempt_count VARCHAR(50) NOT NULL DEFAULT '0',
    last_error TEXT,
    handler_name VARCHAR(255),
    payload TEXT
);

CREATE INDEX IF NOT EXISTS ix_inbox_event_type ON inbox_messages(event_type);
CREATE INDEX IF NOT EXISTS ix_inbox_topic ON inbox_messages(topic);
CREATE INDEX IF NOT EXISTS ix_inbox_correlation_id ON inbox_messages(correlation_id);
CREATE INDEX IF NOT EXISTS ix_inbox_status ON inbox_messages(status);
CREATE INDEX IF NOT EXISTS ix_inbox_received_at ON inbox_messages(received_at);
CREATE INDEX IF NOT EXISTS ix_inbox_locked_until ON inbox_messages(locked_until);
CREATE INDEX IF NOT EXISTS ix_inbox_status_received ON inbox_messages(status, received_at);
CREATE INDEX IF NOT EXISTS ix_inbox_topic_partition_offset ON inbox_messages(topic, partition, offset);
"""
