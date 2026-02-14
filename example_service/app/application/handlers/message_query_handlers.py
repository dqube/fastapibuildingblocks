"""Query handlers for message retrieval."""

import logging
from typing import List, Optional

from building_blocks.application import QueryHandler
from ...domain.entities.message import Message
from ...infrastructure.persistence.repositories.message_repository import MessageRepository
from ..queries.message_queries import (
    GetAllMessagesQuery,
    GetMessagesBySenderQuery,
    GetMessageByIdQuery,
)

# Import observability modules (optional)
try:
    from building_blocks.observability.logging import get_logger
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False
    get_logger = None

logger = get_logger(__name__) if OBSERVABILITY_AVAILABLE else logging.getLogger(__name__)


class GetAllMessagesQueryHandler(QueryHandler[List[Message]]):
    """Handler for retrieving all messages."""
    
    def __init__(self, repository: MessageRepository):
        """
        Initialize handler.
        
        Args:
            repository: Message repository
        """
        self.repository = repository
    
    async def handle(self, query: GetAllMessagesQuery) -> List[Message]:
        """
        Handle the query.
        
        Args:
            query: Query to get all messages
            
        Returns:
            List of messages
        """
        logger.info("Retrieving all messages", extra={"extra_fields": {"limit": query.limit}})
        messages = await self.repository.get_recent_messages(limit=query.limit)
        logger.info("Retrieved messages", extra={"extra_fields": {"count": len(messages)}})
        return messages


class GetMessagesBySenderQueryHandler(QueryHandler[List[Message]]):
    """Handler for retrieving messages by sender."""
    
    def __init__(self, repository: MessageRepository):
        """
        Initialize handler.
        
        Args:
            repository: Message repository
        """
        self.repository = repository
    
    async def handle(self, query: GetMessagesBySenderQuery) -> List[Message]:
        """
        Handle the query.
        
        Args:
            query: Query to get messages by sender
            
        Returns:
            List of messages from the sender
        """
        logger.info("Retrieving messages by sender", extra={"extra_fields": {"sender": query.sender, "limit": query.limit}})
        messages = await self.repository.find_by_sender(query.sender, limit=query.limit)
        logger.info("Retrieved messages by sender", extra={"extra_fields": {"sender": query.sender, "count": len(messages)}})
        return messages


class GetMessageByIdQueryHandler(QueryHandler[Optional[Message]]):
    """Handler for retrieving a specific message."""
    
    def __init__(self, repository: MessageRepository):
        """
        Initialize handler.
        
        Args:
            repository: Message repository
        """
        self.repository = repository
    
    async def handle(self, query: GetMessageByIdQuery) -> Optional[Message]:
        """
        Handle the query.
        
        Args:
            query: Query to get a message by ID
            
        Returns:
            Message if found, None otherwise
        """
        logger.info("Retrieving message by ID", extra={"extra_fields": {"message_id": str(query.message_id)}})
        message = await self.repository.find_by_message_id(query.message_id)
        if message:
            logger.info("Message found", extra={"extra_fields": {"message_id": str(query.message_id)}})
        else:
            logger.warning("Message not found", extra={"extra_fields": {"message_id": str(query.message_id)}})
        return message
