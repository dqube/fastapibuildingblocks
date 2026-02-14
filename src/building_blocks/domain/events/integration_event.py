"""Integration Event base class for cross-service communication."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class IntegrationEvent(BaseModel):
    """
    Base class for all integration events.
    
    Integration events represent domain events that cross bounded context boundaries.
    They are used to communicate state changes between microservices via message brokers
    (like Kafka, RabbitMQ, etc.).
    
    Similar to Wolverine's integration events in .NET, these events:
    - Are published to external message brokers
    - Support serialization/deserialization
    - Include metadata for routing and tracking
    - Enable asynchronous cross-service communication
    """
    
    event_id: UUID = Field(default_factory=uuid4, description="Unique identifier for this event")
    occurred_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the event occurred"
    )
    event_type: str = Field(default="", description="Type name of the event")
    event_version: str = Field(default="1.0", description="Version of the event schema")
    
    # Metadata for routing and tracking
    correlation_id: Optional[UUID] = Field(
        default=None,
        description="Correlation ID for tracking related events across services"
    )
    causation_id: Optional[UUID] = Field(
        default=None,
        description="ID of the event that caused this event"
    )
    source_service: Optional[str] = Field(
        default=None,
        description="Name of the service that published this event"
    )
    
    # Aggregate information (optional)
    aggregate_id: Optional[UUID] = Field(
        default=None,
        description="ID of the aggregate this event relates to"
    )
    aggregate_type: Optional[str] = Field(
        default=None,
        description="Type name of the aggregate"
    )
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
    
    def __init__(self, **data: Any):
        """Initialize the integration event with event type."""
        super().__init__(**data)
        if not self.event_type:
            self.event_type = self.__class__.__name__
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the integration event to a dictionary.
        
        Returns:
            Dictionary representation of the integration event
        """
        return self.model_dump(mode='json')
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IntegrationEvent":
        """
        Create an integration event from a dictionary.
        
        Args:
            data: Dictionary containing event data
            
        Returns:
            Integration event instance
        """
        return cls(**data)
    
    def get_topic_name(self) -> str:
        """
        Get the Kafka topic name for this event.
        
        By default, uses the event type in snake_case.
        Override this method to customize topic naming.
        
        Returns:
            Kafka topic name
        """
        # Convert CamelCase to snake_case
        import re
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', self.event_type)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
        return f"integration-events.{name}"
    
    def get_partition_key(self) -> Optional[str]:
        """
        Get the partition key for Kafka partitioning.
        
        By default, uses aggregate_id if available.
        Override this method to customize partitioning strategy.
        
        Returns:
            Partition key as string, or None for random partitioning
        """
        if self.aggregate_id:
            return str(self.aggregate_id)
        return None


class IntegrationEventEnvelope(BaseModel):
    """
    Envelope wrapper for integration events with metadata.
    
    This wrapper adds transport-level metadata around the actual event payload.
    """
    
    event_id: UUID
    event_type: str
    event_version: str
    occurred_at: datetime
    correlation_id: Optional[UUID] = None
    causation_id: Optional[UUID] = None
    source_service: Optional[str] = None
    
    # The actual event payload
    payload: Dict[str, Any]
    
    # Metadata
    content_type: str = "application/json"
    schema_version: str = "1.0"
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
    
    @classmethod
    def wrap(cls, event: IntegrationEvent) -> "IntegrationEventEnvelope":
        """
        Wrap an integration event in an envelope.
        
        Args:
            event: The integration event to wrap
            
        Returns:
            Event envelope
        """
        return cls(
            event_id=event.event_id,
            event_type=event.event_type,
            event_version=event.event_version,
            occurred_at=event.occurred_at,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            source_service=event.source_service,
            payload=event.to_dict(),
        )
    
    def to_json(self) -> str:
        """
        Serialize envelope to JSON string.
        
        Returns:
            JSON string representation
        """
        return self.model_dump_json()
    
    @classmethod
    def from_json(cls, json_str: str) -> "IntegrationEventEnvelope":
        """
        Deserialize envelope from JSON string.
        
        Args:
            json_str: JSON string
            
        Returns:
            Event envelope instance
        """
        return cls.model_validate_json(json_str)
