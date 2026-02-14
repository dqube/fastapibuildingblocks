"""Base Entity class for domain entities."""

from abc import ABC
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class BaseEntity(BaseModel, ABC):
    """
    Base class for all domain entities.
    
    An entity is an object that has a unique identity and a lifecycle.
    Entities are distinguished by their ID, not their attributes.
    """
    
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        arbitrary_types_allowed = True
        validate_assignment = True
    
    def __eq__(self, other: Any) -> bool:
        """
        Entities are equal if they have the same ID.
        
        Args:
            other: The other object to compare with
            
        Returns:
            True if the entities have the same ID, False otherwise
        """
        if not isinstance(other, BaseEntity):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """
        Hash based on entity ID.
        
        Returns:
            Hash of the entity ID
        """
        return hash(self.id)
    
    def update_timestamp(self) -> None:
        """Update the updated_at timestamp to the current time."""
        self.updated_at = datetime.utcnow()
