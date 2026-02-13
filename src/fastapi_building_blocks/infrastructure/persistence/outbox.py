"""
Outbox pattern implementation for reliable event publishing.

The outbox pattern ensures that integration events are not lost by storing them
in a database table before publishing to Kafka. A background worker (relay) 
reads from the outbox and publishes to Kafka, ensuring at-least-once delivery.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4
import json

from sqlalchemy import Column, String, DateTime, Text, Index, Boolean, Integer, select, delete
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class OutboxStatus(str, Enum):
    """Status of an outbox message."""
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"


class OutboxMessage(Base):
    """
    Outbox table for storing integration events before publishing.
    
    This ensures that events are persisted atomically with business data
    and will be eventually published even if the service crashes.
    
    Workflow:
    1. Business logic executes and saves data
    2. Integration events are saved to outbox (same transaction)
    3. Transaction commits
    4. Outbox relay reads pending messages and publishes to Kafka
    5. Message status updated to 'published'
    """
    
    __tablename__ = "outbox_messages"
    
    # Primary key
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Event metadata
    event_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    event_type = Column(String(255), nullable=False, index=True)
    event_version = Column(String(50), nullable=False, default="1.0")
    
    # Routing information
    topic = Column(String(255), nullable=False, index=True)
    partition_key = Column(String(255), nullable=True)
    
    # Event data
    payload = Column(Text, nullable=False)  # JSON serialized event
    headers = Column(Text, nullable=True)   # JSON serialized headers
    
    # Correlation tracking
    correlation_id = Column(PG_UUID(as_uuid=True), nullable=True, index=True)
    causation_id = Column(PG_UUID(as_uuid=True), nullable=True)
    
    # Processing metadata
    status = Column(String(50), nullable=False, default=OutboxStatus.PENDING, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    published_at = Column(DateTime, nullable=True)
    locked_until = Column(DateTime, nullable=True, index=True)
    
    # Retry tracking
    attempt_count = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)
    
    # Source tracking
    source_service = Column(String(255), nullable=True)
    aggregate_id = Column(PG_UUID(as_uuid=True), nullable=True, index=True)
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('ix_outbox_status_created', 'status', 'created_at'),
        Index('ix_outbox_pending_locked', 'status', 'locked_until'),
    )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': str(self.id),
            'event_id': str(self.event_id),
            'event_type': self.event_type,
            'event_version': self.event_version,
            'topic': self.topic,
            'partition_key': self.partition_key,
            'payload': self.payload,
            'headers': self.headers,
            'correlation_id': str(self.correlation_id) if self.correlation_id else None,
            'causation_id': str(self.causation_id) if self.causation_id else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'attempt_count': self.attempt_count,
            'last_error': self.last_error,
            'source_service': self.source_service,
            'aggregate_id': str(self.aggregate_id) if self.aggregate_id else None,
        }


class OutboxRepository:
    """Repository for managing outbox messages."""
    
    def __init__(self, session):
        """
        Initialize repository.
        
        Args:
            session: SQLAlchemy session
        """
        self.session = session
    
    async def add(self, message: OutboxMessage) -> None:
        """
        Add a message to the outbox.
        
        Args:
            message: Outbox message to add
        """
        self.session.add(message)
    
    async def add_many(self, messages: List[OutboxMessage]) -> None:
        """
        Add multiple messages to the outbox.
        
        Args:
            messages: List of outbox messages
        """
        self.session.add_all(messages)
    
    async def get_pending_messages(
        self,
        limit: int = 100,
        lock_duration_seconds: int = 300
    ) -> List[OutboxMessage]:
        """
        Get pending messages for publishing.
        
        Uses pessimistic locking to prevent duplicate processing.
        
        Args:
            limit: Maximum number of messages to retrieve
            lock_duration_seconds: How long to lock messages (prevents other workers from processing)
            
        Returns:
            List of pending outbox messages
        """
        now = datetime.utcnow()
        lock_until = now + timedelta(seconds=lock_duration_seconds)
        
        # Find pending messages that are not currently locked
        messages = (
            self.session.query(OutboxMessage)
            .filter(
                OutboxMessage.status == OutboxStatus.PENDING,
                (OutboxMessage.locked_until.is_(None) | (OutboxMessage.locked_until < now))
            )
            .order_by(OutboxMessage.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)  # Skip locked rows
            .all()
        )
        
        # Lock the messages
        for message in messages:
            message.locked_until = lock_until
        
        return messages
    
    async def mark_as_published(self, message_id: UUID) -> None:
        """
        Mark a message as successfully published.
        
        Args:
            message_id: ID of the message
        """
        message = self.session.query(OutboxMessage).filter(OutboxMessage.id == message_id).first()
        if message:
            message.status = OutboxStatus.PUBLISHED
            message.published_at = datetime.utcnow()
    
    async def mark_as_failed(
        self,
        message_id: UUID,
        error: str,
        max_attempts: int = 3
    ) -> None:
        """
        Mark a message as failed.
        
        Args:
            message_id: ID of the message
            error: Error message
            max_attempts: Maximum retry attempts before permanent failure
        """
        message = self.session.query(OutboxMessage).filter(OutboxMessage.id == message_id).first()
        if message:
            message.attempt_count = message.attempt_count + 1
            message.last_error = error
            message.locked_until = None
            
            # If max attempts exceeded, mark as permanently failed
            if message.attempt_count >= max_attempts:
                message.status = OutboxStatus.FAILED
    
    async def cleanup_old_messages(self, days: int = 7) -> int:
        """
        Clean up old published messages.
        
        Args:
            days: Delete messages older than this many days
            
        Returns:
            Number of messages deleted
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        deleted = (
            self.session.query(OutboxMessage)
            .filter(
                OutboxMessage.status == OutboxStatus.PUBLISHED,
                OutboxMessage.published_at < cutoff
            )
            .delete()
        )
        
        return deleted
    
    async def get_failed_messages(self, limit: int = 100) -> List[OutboxMessage]:
        """
        Get failed messages for inspection.
        
        Args:
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of failed messages
        """
        return (
            self.session.query(OutboxMessage)
            .filter(OutboxMessage.status == OutboxStatus.FAILED)
            .order_by(OutboxMessage.created_at.desc())
            .limit(limit)
            .all()
        )
    
    async def retry_failed_message(self, message_id: UUID) -> None:
        """
        Reset a failed message to pending for retry.
        
        Args:
            message_id: ID of the message
        """
        message = self.session.query(OutboxMessage).filter(OutboxMessage.id == message_id).first()
        if message:
            message.status = OutboxStatus.PENDING
            message.locked_until = None
            message.last_error = None


# SQL for creating the table (PostgreSQL)
CREATE_OUTBOX_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS outbox_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL,
    event_type VARCHAR(255) NOT NULL,
    event_version VARCHAR(50) NOT NULL DEFAULT '1.0',
    topic VARCHAR(255) NOT NULL,
    partition_key VARCHAR(255),
    payload TEXT NOT NULL,
    headers TEXT,
    correlation_id UUID,
    causation_id UUID,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    published_at TIMESTAMP,
    locked_until TIMESTAMP,
    attempt_count VARCHAR(50) NOT NULL DEFAULT '0',
    last_error TEXT,
    source_service VARCHAR(255),
    aggregate_id UUID
);

CREATE INDEX IF NOT EXISTS ix_outbox_event_id ON outbox_messages(event_id);
CREATE INDEX IF NOT EXISTS ix_outbox_event_type ON outbox_messages(event_type);
CREATE INDEX IF NOT EXISTS ix_outbox_topic ON outbox_messages(topic);
CREATE INDEX IF NOT EXISTS ix_outbox_correlation_id ON outbox_messages(correlation_id);
CREATE INDEX IF NOT EXISTS ix_outbox_status ON outbox_messages(status);
CREATE INDEX IF NOT EXISTS ix_outbox_created_at ON outbox_messages(created_at);
CREATE INDEX IF NOT EXISTS ix_outbox_locked_until ON outbox_messages(locked_until);
CREATE INDEX IF NOT EXISTS ix_outbox_aggregate_id ON outbox_messages(aggregate_id);
CREATE INDEX IF NOT EXISTS ix_outbox_status_created ON outbox_messages(status, created_at);
CREATE INDEX IF NOT EXISTS ix_outbox_pending_locked ON outbox_messages(status, locked_until);
"""
