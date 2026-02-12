"""User-related domain events."""

from uuid import UUID
from fastapi_building_blocks.domain import DomainEvent


class UserCreatedEvent(DomainEvent):
    """Event raised when a new user is created."""
    
    email: str
    full_name: str


class UserUpdatedEvent(DomainEvent):
    """Event raised when a user is updated."""
    
    full_name: str


class UserDeletedEvent(DomainEvent):
    """Event raised when a user is deleted/deactivated."""
    
    email: str
