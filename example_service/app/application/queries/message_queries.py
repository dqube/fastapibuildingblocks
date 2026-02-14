"""Queries for retrieving messages."""

from typing import Optional
from uuid import UUID

from fastapi_building_blocks.application import Query


class GetAllMessagesQuery(Query):
    """Query to get all received messages."""
    
    limit: int = 100


class GetMessagesBySenderQuery(Query):
    """Query to get messages from a specific sender."""
    
    sender: str
    limit: int = 100


class GetMessageByIdQuery(Query):
    """Query to get a specific message by ID."""
    
    message_id: UUID
