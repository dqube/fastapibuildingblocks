"""Base classes for mediator pattern."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar, Union

from pydantic import BaseModel

# Type variables for generic typing
TRequest = TypeVar("TRequest", bound="Request")
TResponse = TypeVar("TResponse")


class Request(BaseModel, ABC):
    """
    Base class for all requests (commands and queries) in the mediator pattern.
    
    This provides a unified interface for both commands and queries,
    allowing them to be processed through the same mediator.
    """
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        arbitrary_types_allowed = True


class RequestHandler(ABC, Generic[TRequest, TResponse]):
    """
    Base class for request handlers in the mediator pattern.
    
    Request handlers process requests and return responses.
    Each handler should handle exactly one type of request.
    """
    
    @abstractmethod
    async def handle(self, request: TRequest) -> TResponse:
        """
        Handle the request.
        
        Args:
            request: The request to handle
            
        Returns:
            The response from handling the request
        """
        pass


class IMediator(ABC):
    """
    Interface for the mediator pattern.
    
    The mediator routes requests (commands and queries) to their appropriate handlers.
    It acts as a central dispatcher, decoupling the sender from the receiver.
    """
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def register_handler(
        self, 
        request_type: type[Request], 
        handler: RequestHandler[Any, Any]
    ) -> None:
        """
        Register a handler for a specific request type.
        
        Args:
            request_type: The type of request to handle
            handler: The handler instance
        """
        pass
    
    @abstractmethod
    def register_handler_factory(
        self,
        request_type: type[Request],
        factory: callable
    ) -> None:
        """
        Register a handler factory for a specific request type.
        
        The factory will be called each time a request needs to be handled,
        allowing for dependency injection and handler lifecycle management.
        
        Args:
            request_type: The type of request to handle
            factory: A callable that returns a handler instance
        """
        pass
