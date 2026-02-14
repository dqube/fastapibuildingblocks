"""Repository for Message entity."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import Table, Column, String, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from building_blocks.infrastructure import SQLAlchemyRepository, Base
from ....domain.entities.message import Message


# SQLAlchemy Table definition
messages_table = Table(
    'messages',
    Base.metadata,
    Column('id', PGUUID(as_uuid=True), primary_key=True),
    Column('message_id', PGUUID(as_uuid=True), unique=True, nullable=False, index=True),
    Column('content', Text, nullable=False),
    Column('sender', String(255), nullable=False, index=True),
    Column('timestamp', DateTime, nullable=False, index=True),
    Column('metadata', JSON, nullable=True),
    Column('processed_at', DateTime, nullable=False),
    Column('created_at', DateTime, nullable=False),
    Column('updated_at', DateTime, nullable=False),
    extend_existing=True,
)


class MessageRepository(SQLAlchemyRepository[Message]):
    """Repository for managing message persistence."""
    
    table = messages_table
    
    def __init__(self, session: AsyncSession):
        """
        Initialize the message repository.
        
        Args:
            session: Database session
        """
        super().__init__(session)
    
    def _row_to_entity(self, row) -> Message:
        """Convert database row to entity."""
        return Message(
            id=row.id,
            message_id=row.message_id,
            content=row.content,
            sender=row.sender,
            timestamp=row.timestamp,
            metadata=row.metadata or {},
            processed_at=row.processed_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
    
    def _entity_to_dict(self, entity: Message) -> dict:
        """Convert entity to dictionary for database storage."""
        return {
            'id': entity.id,
            'message_id': entity.message_id,
            'content': entity.content,
            'sender': entity.sender,
            'timestamp': entity.timestamp,
            'metadata': entity.metadata,
            'processed_at': entity.processed_at,
            'created_at': entity.created_at,
            'updated_at': entity.updated_at,
        }
    
    async def find_by_message_id(self, message_id: UUID) -> Optional[Message]:
        """
        Find a message by its message ID.
        
        Args:
            message_id: Message ID to search for
            
        Returns:
            Message if found, None otherwise
        """
        result = await self._session.execute(
            select(self.table).where(self.table.c.message_id == message_id)
        )
        row = result.first()
        return self._row_to_entity(row) if row else None
    
    async def find_by_sender(self, sender: str, limit: int = 100) -> List[Message]:
        """
        Find messages by sender.
        
        Args:
            sender: Sender to search for
            limit: Maximum number of messages to return
            
        Returns:
            List of messages from the sender
        """
        result = await self._session.execute(
            select(self.table)
            .where(self.table.c.sender == sender)
            .order_by(self.table.c.timestamp.desc())
            .limit(limit)
        )
        return [self._row_to_entity(row) for row in result]
    
    async def get_recent_messages(self, limit: int = 100) -> List[Message]:
        """
        Get the most recent messages.
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List of recent messages
        """
        result = await self._session.execute(
            select(self.table)
            .order_by(self.table.c.timestamp.desc())
            .limit(limit)
        )
        return [self._row_to_entity(row) for row in result]
