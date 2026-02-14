"""Base messaging interfaces for event bus and message queue."""

from abc import ABC, abstractmethod
from typing import Any, Callable, List

from ...domain.events.base import DomainEvent


class IEventPublisher(ABC):
    """
    Interface for publishing domain events.
    
    Event publishers broadcast domain events to interested subscribers.
    """
    
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """
        Publish a domain event.
        
        Args:
            event: The domain event to publish
        """
        pass
    
    @abstractmethod
    async def publish_many(self, events: List[DomainEvent]) -> None:
        """
        Publish multiple domain events.
        
        Args:
            events: List of domain events to publish
        """
        pass


class IMessageBus(ABC):
    """
    Interface for message bus (event bus).
    
    The message bus routes messages (events, commands) to their appropriate handlers.
    """
    
    @abstractmethod
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """
        Subscribe a handler to an event type.
        
        Args:
            event_type: The type of event to subscribe to
            handler: The handler function to call when the event occurs
        """
        pass
    
    @abstractmethod
    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """
        Unsubscribe a handler from an event type.
        
        Args:
            event_type: The type of event to unsubscribe from
            handler: The handler function to remove
        """
        pass
    
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event: The event to publish
        """
        pass
    
    @abstractmethod
    async def send(self, message: Any) -> Any:
        """
        Send a message (command/query) to its handler.
        
        Args:
            message: The message to send
            
        Returns:
            The result from the message handler
        """
        pass
