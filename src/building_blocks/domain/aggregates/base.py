"""Base AggregateRoot class for domain aggregates."""

from typing import List

from ..entities.base import BaseEntity
from ..events.base import DomainEvent


class AggregateRoot(BaseEntity):
    """
    Base class for aggregate roots.
    
    An aggregate root is a cluster of domain objects that can be treated as a single unit.
    All external access to the aggregate goes through the aggregate root.
    The aggregate root ensures the consistency of changes within the aggregate boundary.
    """
    
    def __init__(self, **data):
        """Initialize the aggregate root with empty domain events list."""
        super().__init__(**data)
        self._domain_events: List[DomainEvent] = []
    
    def add_domain_event(self, event: DomainEvent) -> None:
        """
        Add a domain event to the aggregate.
        
        Args:
            event: The domain event to add
        """
        self._domain_events.append(event)
    
    def clear_domain_events(self) -> None:
        """Clear all domain events from the aggregate."""
        self._domain_events.clear()
    
    def get_domain_events(self) -> List[DomainEvent]:
        """
        Get all domain events from the aggregate.
        
        Returns:
            List of domain events
        """
        return self._domain_events.copy()
    
    @property
    def domain_events(self) -> List[DomainEvent]:
        """
        Get all domain events from the aggregate.
        
        Returns:
            List of domain events
        """
        return self.get_domain_events()
