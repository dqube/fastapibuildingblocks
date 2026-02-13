"""Handler registry for mediator pattern."""

from typing import Any, Callable, Dict, Optional, Union

from .base import Request, RequestHandler


class HandlerRegistry:
    """
    Registry for mapping request types to their handlers.
    
    Supports both static handler instances and handler factories
    for more flexible dependency injection.
    """
    
    def __init__(self) -> None:
        """Initialize the handler registry."""
        self._handlers: Dict[type[Request], RequestHandler[Any, Any]] = {}
        self._factories: Dict[type[Request], Callable[[], RequestHandler[Any, Any]]] = {}
    
    def register(
        self, 
        request_type: type[Request], 
        handler: RequestHandler[Any, Any]
    ) -> None:
        """
        Register a handler instance for a request type.
        
        Args:
            request_type: The type of request to handle
            handler: The handler instance
            
        Raises:
            ValueError: If a handler is already registered for this type
        """
        if request_type in self._handlers or request_type in self._factories:
            raise ValueError(
                f"Handler already registered for {request_type.__name__}"
            )
        
        self._handlers[request_type] = handler
    
    def register_factory(
        self,
        request_type: type[Request],
        factory: Callable[[], RequestHandler[Any, Any]]
    ) -> None:
        """
        Register a handler factory for a request type.
        
        The factory will be called each time a handler is needed,
        allowing for dependency injection and lifecycle management.
        
        Args:
            request_type: The type of request to handle
            factory: A callable that returns a handler instance
            
        Raises:
            ValueError: If a handler is already registered for this type
        """
        if request_type in self._handlers or request_type in self._factories:
            raise ValueError(
                f"Handler already registered for {request_type.__name__}"
            )
        
        self._factories[request_type] = factory
    
    def get_handler(
        self, 
        request_type: type[Request]
    ) -> Optional[RequestHandler[Any, Any]]:
        """
        Get a handler for a request type.
        
        If a factory is registered, it will be called to create the handler.
        If a handler instance is registered, it will be returned directly.
        
        Args:
            request_type: The type of request
            
        Returns:
            The handler instance, or None if not found
        """
        # Check for factory first (allows for dependency injection)
        if request_type in self._factories:
            factory = self._factories[request_type]
            return factory()
        
        # Fall back to static handler instance
        return self._handlers.get(request_type)
    
    def has_handler(self, request_type: type[Request]) -> bool:
        """
        Check if a handler is registered for a request type.
        
        Args:
            request_type: The type of request
            
        Returns:
            True if a handler is registered, False otherwise
        """
        return (
            request_type in self._handlers or 
            request_type in self._factories
        )
    
    def clear(self) -> None:
        """Clear all registered handlers and factories."""
        self._handlers.clear()
        self._factories.clear()
    
    def unregister(self, request_type: type[Request]) -> None:
        """
        Unregister a handler for a request type.
        
        Args:
            request_type: The type of request
        """
        self._handlers.pop(request_type, None)
        self._factories.pop(request_type, None)
