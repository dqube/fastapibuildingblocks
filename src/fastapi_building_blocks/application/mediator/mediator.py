"""Mediator implementation."""

import time
from typing import Any, Callable, Optional

from .base import IMediator, Request, RequestHandler
from .registry import HandlerRegistry


# Import observability modules (optional)
try:
    from ...observability.tracing import get_tracer
    from ...observability.logging import get_logger
    from ...observability.metrics import record_mediator_request
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False
    get_tracer = None
    get_logger = None
    record_mediator_request = None


logger = get_logger(__name__) if OBSERVABILITY_AVAILABLE else None


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
        
        This method automatically instruments the request with:
        - Distributed tracing (span creation)
        - Structured logging
        - Metrics collection (duration, success/error counts)
        
        Args:
            request: The request to send (command or query)
            
        Returns:
            The result from the handler
            
        Raises:
            ValueError: If no handler is registered for the request type
        """
        request_type = type(request)
        request_name = request_type.__name__
        
        handler = self._registry.get_handler(request_type)
        
        if handler is None:
            raise ValueError(
                f"No handler registered for request type: {request_name}. "
                f"Make sure to register a handler using register_handler() or "
                f"register_handler_factory() before sending requests."
            )
        
        handler_name = type(handler).__name__
        
        # Start tracing span if observability is available
        if OBSERVABILITY_AVAILABLE and get_tracer:
            tracer = get_tracer(__name__)
            with tracer.start_as_current_span(f"mediator.send.{request_name}") as span:
                # Add span attributes
                span.set_attribute("mediator.request_type", request_name)
                span.set_attribute("mediator.handler_type", handler_name)
                span.set_attribute("mediator.request_module", request_type.__module__)
                
                # Execute with instrumentation
                return await self._execute_with_instrumentation(
                    request, handler, request_name, handler_name, span
                )
        else:
            # Execute without tracing
            return await self._execute_with_instrumentation(
                request, handler, request_name, handler_name, None
            )
    
    async def _execute_with_instrumentation(
        self, 
        request: Request, 
        handler: RequestHandler[Any, Any],
        request_name: str,
        handler_name: str,
        span: Optional[Any] = None
    ) -> Any:
        """Execute handler with full instrumentation."""
        start_time = time.time()
        error_type: Optional[str] = None
        success = False
        
        try:
            # Log request start
            if logger:
                logger.info(
                    f"Mediator processing request: {request_name}",
                    extra={
                        "extra_fields": {
                            "mediator.request_type": request_name,
                            "mediator.handler_type": handler_name,
                        }
                    },
                )
            
            # Execute handler
            result = await handler.handle(request)
            success = True
            
            # Update span on success
            if span:
                span.set_attribute("mediator.success", True)
            
            # Log success
            if logger:
                duration = time.time() - start_time
                logger.info(
                    f"Mediator completed request: {request_name}",
                    extra={
                        "extra_fields": {
                            "mediator.request_type": request_name,
                            "mediator.handler_type": handler_name,
                            "mediator.duration_seconds": duration,
                            "mediator.success": True,
                        }
                    },
                )
            
            return result
            
        except Exception as e:
            error_type = type(e).__name__
            success = False
            
            # Update span on error
            if span:
                span.set_attribute("mediator.success", False)
                span.set_attribute("mediator.error_type", error_type)
                span.record_exception(e)
            
            # Log error
            if logger:
                duration = time.time() - start_time
                logger.error(
                    f"Mediator error processing request: {request_name}",
                    exc_info=True,
                    extra={
                        "extra_fields": {
                            "mediator.request_type": request_name,
                            "mediator.handler_type": handler_name,
                            "mediator.duration_seconds": duration,
                            "mediator.error_type": error_type,
                        }
                    },
                )
            
            raise
            
        finally:
            # Record metrics
            if OBSERVABILITY_AVAILABLE and record_mediator_request:
                duration = time.time() - start_time
                record_mediator_request(
                    request_type=request_name,
                    handler=handler_name,
                    duration=duration,
                    success=success,
                    error_type=error_type,
                )
    
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
