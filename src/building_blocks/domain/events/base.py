"""Base DomainEvent class for domain events."""

from datetime import datetime
from typing import Any, Dict
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    """
    Base class for all domain events.
    
    Domain events represent something that happened in the domain that domain experts
    care about. They are used to communicate state changes and trigger side effects.
    """
    
    event_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    aggregate_id: UUID | None = None
    event_type: str = Field(default="")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        arbitrary_types_allowed = True
    
    def __init__(self, **data: Any):
        """Initialize the domain event with event type."""
        super().__init__(**data)
        if not self.event_type:
            self.event_type = self.__class__.__name__
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the domain event to a dictionary.
        
        Returns:
            Dictionary representation of the domain event
        """
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainEvent":
        """
        Create a domain event from a dictionary.
        
        Args:
            data: Dictionary containing event data
            
        Returns:
            Domain event instance
        """
        return cls(**data)
