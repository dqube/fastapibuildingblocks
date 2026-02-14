"""Event mapping and transformation utilities."""

from typing import Optional, Type, Callable, Dict
from uuid import UUID

from ...domain.events.base import DomainEvent
from ...domain.events.integration_event import IntegrationEvent


class EventMapper:
    """
    Maps domain events to integration events.
    
    This utility helps convert internal domain events to integration events
    that can be published to external message brokers. Similar to Wolverine's
    event transformation capabilities.
    
    Example:
        >>> mapper = EventMapper()
        >>> mapper.register_mapping(UserCreatedEvent, UserCreatedIntegrationEvent)
        >>> integration_event = mapper.map(domain_event)
    """
    
    def __init__(self):
        """Initialize the event mapper."""
        self._mappings: Dict[Type[DomainEvent], Callable[[DomainEvent], IntegrationEvent]] = {}
    
    def register_mapping(
        self,
        domain_event_type: Type[DomainEvent],
        integration_event_type: Type[IntegrationEvent],
        transform: Optional[Callable[[DomainEvent], Dict]] = None,
    ) -> None:
        """
        Register a mapping from domain event to integration event.
        
        Args:
            domain_event_type: The domain event class
            integration_event_type: The integration event class
            transform: Optional transformation function to customize mapping
        """
        def mapper(domain_event: DomainEvent) -> IntegrationEvent:
            if transform:
                # Use custom transformation
                data = transform(domain_event)
            else:
                # Default: copy all fields from domain event
                data = domain_event.model_dump()
            
            # Create integration event with transformed data
            integration_event = integration_event_type(**data)
            
            # Preserve event metadata
            integration_event.event_id = domain_event.event_id
            integration_event.occurred_at = domain_event.occurred_at
            integration_event.aggregate_id = domain_event.aggregate_id
            
            return integration_event
        
        self._mappings[domain_event_type] = mapper
    
    def register_mapping_function(
        self,
        domain_event_type: Type[DomainEvent],
        mapper_func: Callable[[DomainEvent], IntegrationEvent],
    ) -> None:
        """
        Register a custom mapping function.
        
        Args:
            domain_event_type: The domain event class
            mapper_func: Function that maps domain event to integration event
        """
        self._mappings[domain_event_type] = mapper_func
    
    def map(self, domain_event: DomainEvent) -> Optional[IntegrationEvent]:
        """
        Map a domain event to an integration event.
        
        Args:
            domain_event: The domain event to map
            
        Returns:
            Integration event if mapping exists, None otherwise
        """
        domain_event_type = type(domain_event)
        
        if domain_event_type not in self._mappings:
            return None
        
        mapper = self._mappings[domain_event_type]
        return mapper(domain_event)
    
    def has_mapping(self, domain_event_type: Type[DomainEvent]) -> bool:
        """
        Check if a mapping exists for a domain event type.
        
        Args:
            domain_event_type: The domain event class
            
        Returns:
            True if mapping exists, False otherwise
        """
        return domain_event_type in self._mappings


class IntegrationEventFactory:
    """
    Factory for creating integration events with consistent metadata.
    
    This factory ensures that all integration events have consistent
    correlation IDs, causation IDs, and source service information.
    """
    
    def __init__(self, service_name: str):
        """
        Initialize the factory.
        
        Args:
            service_name: Name of this service
        """
        self.service_name = service_name
    
    def create_from_domain_event(
        self,
        integration_event_type: Type[IntegrationEvent],
        domain_event: DomainEvent,
        correlation_id: Optional[UUID] = None,
        **kwargs,
    ) -> IntegrationEvent:
        """
        Create an integration event from a domain event.
        
        Args:
            integration_event_type: The integration event class to create
            domain_event: The source domain event
            correlation_id: Optional correlation ID for tracking
            **kwargs: Additional fields for the integration event
            
        Returns:
            New integration event instance
        """
        # Merge domain event data with additional kwargs
        data = domain_event.model_dump()
        data.update(kwargs)
        
        # Create integration event
        integration_event = integration_event_type(**data)
        
        # Set metadata
        integration_event.source_service = self.service_name
        integration_event.correlation_id = correlation_id or domain_event.event_id
        integration_event.causation_id = domain_event.event_id
        integration_event.aggregate_id = domain_event.aggregate_id
        
        return integration_event
    
    def create(
        self,
        integration_event_type: Type[IntegrationEvent],
        correlation_id: Optional[UUID] = None,
        causation_id: Optional[UUID] = None,
        **kwargs,
    ) -> IntegrationEvent:
        """
        Create a new integration event.
        
        Args:
            integration_event_type: The integration event class to create
            correlation_id: Optional correlation ID for tracking
            causation_id: Optional causation ID
            **kwargs: Fields for the integration event
            
        Returns:
            New integration event instance
        """
        integration_event = integration_event_type(**kwargs)
        
        # Set metadata
        integration_event.source_service = self.service_name
        integration_event.correlation_id = correlation_id
        integration_event.causation_id = causation_id
        
        return integration_event
