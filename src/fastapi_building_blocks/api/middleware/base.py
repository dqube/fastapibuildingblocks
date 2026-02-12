"""Base middleware class for FastAPI."""

from abc import ABC, abstractmethod
from typing import Callable

from fastapi import Request, Response


class BaseMiddleware(ABC):
    """
    Base class for FastAPI middleware.
    
    Middleware can process requests before they reach the endpoint
    and responses before they're returned to the client.
    """
    
    @abstractmethod
    async def __call__(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process the request and response.
        
        Args:
            request: The incoming request
            call_next: The next middleware or endpoint to call
            
        Returns:
            The response
        """
        pass
