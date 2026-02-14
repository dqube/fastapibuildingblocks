"""Integration event publishing middleware for mediator."""

import logging
from typing import Any, List, Optional

from ...application.mediator.base import Request, RequestHandler
from ...domain.events.base import DomainEvent
from ...domain.events.integration_event import IntegrationEvent
from .base import IEventPublisher
from .event_mapper import EventMapper


# Import observability modules (optional)
try:
    from ...observability.logging import get_logger
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False
    get_logger = None


logger = get_logger(__name__) if OBSERVABILITY_AVAILABLE else logging.getLogger(__name__)


class IntegrationEventPublishingBehavior:
    """
    Mediator behavior that automatically publishes integration events.
    
    This behavior intercepts mediator requests and publishes any integration events
    that result from command/query processing. Similar to Wolverine's automatic
    integration event publishing in .NET.
    
    It can:
    - Automatically map domain events to integration events
    - Publish integration events after successful request processing
    - Handle errors gracefully without affecting request processing
    
    Example:
        >>> behavior = IntegrationEventPublishingBehavior(publisher, mapper)
        >>> mediator.add_behavior(behavior)  # If mediator supports behaviors
        
        Or use directly:
        >>> result = await behavior.handle(request, handler, next_handler)
    """
    
    def __init__(
        self,
        publisher: IEventPublisher,
        mapper: Optional[EventMapper] = None,
        publish_domain_events: bool = True,
    ):
        """
        Initialize the publishing behavior.
        
        Args:
            publisher: Integration event publisher
            mapper: Optional event mapper for domain->integration event mapping
            publish_domain_events: Whether to auto-publish mapped domain events
        """
        self.publisher = publisher
        self.mapper = mapper or EventMapper()
        self.publish_domain_events = publish_domain_events
    
    async def handle(
        self,
        request: Request,
        handler: RequestHandler[Any, Any],
        next_handler: Any = None,
    ) -> Any:
        """
        Handle the request and publish integration events.
        
        Args:
            request: The mediator request
            handler: The request handler
            next_handler: Next handler in the pipeline (if using pipeline pattern)
            
        Returns:
            Result from the handler
        """
        # Execute the handler
        if next_handler:
            result = await next_handler()
        else:
            result = await handler.handle(request)
        
        # After successful execution, publish any integration events
        await self._publish_integration_events(request, result)
        
        return result
    
    async def _publish_integration_events(self, request: Request, result: Any) -> None:
        """Publish integration events from request result."""
        integration_events: List[IntegrationEvent] = []
        
        # Check if result contains integration events
        if hasattr(result, 'integration_events'):
            events = result.integration_events
            if isinstance(events, list):
                integration_events.extend(events)
            elif isinstance(events, IntegrationEvent):
                integration_events.append(events)
        
        # Check if result contains domain events that should be mapped
        if self.publish_domain_events and hasattr(result, 'domain_events'):
            domain_events = result.domain_events
            if isinstance(domain_events, list):
                for domain_event in domain_events:
                    mapped_event = self.mapper.map(domain_event)
                    if mapped_event:
                        integration_events.append(mapped_event)
            elif isinstance(domain_events, DomainEvent):
                mapped_event = self.mapper.map(domain_events)
                if mapped_event:
                    integration_events.append(mapped_event)
        
        # Publish all integration events
        if integration_events:
            try:
                await self.publisher.publish_many(integration_events)
                
                if logger:
                    logger.info(
                        f"Published {len(integration_events)} integration events",
                        extra={
                            "extra_fields": {
                                "request.type": type(request).__name__,
                                "integration_events.count": len(integration_events),
                            }
                        },
                    )
            except Exception as e:
                # Log error but don't fail the request
                logger.error(
                    f"Failed to publish integration events: {e}",
                    extra={
                        "extra_fields": {
                            "request.type": type(request).__name__,
                            "error": str(e),
                        }
                    },
                )


class IntegrationEventMediatorWrapper:
    """
    Wrapper for mediator that adds integration event publishing.
    
    This wrapper decorates a mediator to automatically publish integration events
    after successful command/query processing.
    
    Example:
        >>> mediator = Mediator()
        >>> wrapped_mediator = IntegrationEventMediatorWrapper(mediator, publisher, mapper)
        >>> result = await wrapped_mediator.send(command)
    """
    
    def __init__(
        self,
        mediator: Any,
        publisher: IEventPublisher,
        mapper: Optional[EventMapper] = None,
    ):
        """
        Initialize the wrapper.
        
        Args:
            mediator: The mediator instance to wrap
            publisher: Integration event publisher
            mapper: Optional event mapper
        """
        self.mediator = mediator
        self.behavior = IntegrationEventPublishingBehavior(publisher, mapper)
    
    async def send(self, request: Request) -> Any:
        """
        Send a request through the mediator and publish integration events.
        
        Args:
            request: The request to send
            
        Returns:
            Result from the handler
        """
        # Get the handler from the mediator
        handler = self.mediator._registry.get_handler(type(request))
        
        if handler is None:
            # Delegate to mediator for error handling
            return await self.mediator.send(request)
        
        # Execute with integration event publishing
        result = await self.behavior.handle(request, handler)
        
        return result
    
    def register_handler(self, request_type: Any, handler: Any) -> None:
        """
        Register a handler with the underlying mediator.
        
        Args:
            request_type: The request type
            handler: The handler instance
        """
        self.mediator.register_handler(request_type, handler)
    
    def register_handler_factory(self, request_type: Any, factory: Any) -> None:
        """
        Register a handler factory with the underlying mediator.
        
        Args:
            request_type: The request type
            factory: The handler factory
        """
        self.mediator.register_handler_factory(request_type, factory)


def create_integration_event_mediator(
    mediator: Any,
    publisher: IEventPublisher,
    mapper: Optional[EventMapper] = None,
) -> IntegrationEventMediatorWrapper:
    """
    Factory function to create a mediator with integration event publishing.
    
    Args:
        mediator: The base mediator instance
        publisher: Integration event publisher
        mapper: Optional event mapper
        
    Returns:
        Mediator wrapper with integration event publishing
    """
    return IntegrationEventMediatorWrapper(mediator, publisher, mapper)
