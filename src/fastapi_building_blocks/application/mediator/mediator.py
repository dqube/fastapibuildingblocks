"""Mediator implementation."""

from typing import Any, Callable

from .base import IMediator, Request, RequestHandler
from .registry import HandlerRegistry


class Mediator(IMediator):
    """
    Implementation of the mediator pattern.
    
    The mediator routes requests to their registered handlers using a registry.
    It supports both static handler instances and dynamic handler factories
    for flexible dependency injection patterns.
    
    Example:
        >>> mediator = Mediator()
        >>> mediator.register_handler(CreateUserCommand, create_user_handler)
        >>> result = await mediator.send(CreateUserCommand(email="test@example.com"))
    """
    
    def __init__(self, registry: HandlerRegistry | None = None) -> None:
        """
        Initialize the mediator.
        
        Args:
            registry: Optional handler registry. If not provided, a new one is created.
        """
        self._registry = registry or HandlerRegistry()
    
    async def send(self, request: Request) -> Any:
        """
        Send a request to its handler.
        
        Args:
            request: The request to send (command or query)
            
        Returns:
            The result from the handler
            
        Raises:
            ValueError: If no handler is registered for the request type
        """
        request_type = type(request)
        handler = self._registry.get_handler(request_type)
        
        if handler is None:
            raise ValueError(
                f"No handler registered for request type: {request_type.__name__}. "
                f"Make sure to register a handler using register_handler() or "
                f"register_handler_factory() before sending requests."
            )
        
        return await handler.handle(request)
    
    def register_handler(
        self, 
        request_type: type[Request], 
        handler: RequestHandler[Any, Any]
    ) -> None:
        """
        Register a handler instance for a specific request type.
        
        Use this when you have a handler instance that should be reused
        for all requests of this type.
        
        Args:
            request_type: The type of request to handle
            handler: The handler instance
            
        Raises:
            ValueError: If a handler is already registered for this type
        """
        self._registry.register(request_type, handler)
    
    def register_handler_factory(
        self,
        request_type: type[Request],
        factory: Callable[[], RequestHandler[Any, Any]]
    ) -> None:
        """
        Register a handler factory for a specific request type.
        
        The factory will be called each time a request needs to be handled,
        allowing for dependency injection and handler lifecycle management.
        This is useful when handlers need fresh dependencies per request.
        
        Args:
            request_type: The type of request to handle
            factory: A callable that returns a handler instance
            
        Raises:
            ValueError: If a handler is already registered for this type
        """
        self._registry.register_factory(request_type, factory)
    
    @property
    def registry(self) -> HandlerRegistry:
        """
        Get the handler registry.
        
        Returns:
            The handler registry
        """
        return self._registry
