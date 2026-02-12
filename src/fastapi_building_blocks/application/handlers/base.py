"""Base Handler class for generic message handlers."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

TMessage = TypeVar("TMessage")
TResult = TypeVar("TResult")


class Handler(ABC, Generic[TMessage, TResult]):
    """
    Base class for generic message handlers.
    
    Handlers process messages (commands, queries, events) and return results.
    This provides a common interface for all handler types.
    """
    
    @abstractmethod
    async def handle(self, message: TMessage) -> TResult:
        """
        Handle the message.
        
        Args:
            message: The message to handle
            
        Returns:
            The result of handling the message
        """
        pass
    
    def can_handle(self, message: Any) -> bool:
        """
        Check if this handler can handle the given message.
        
        Args:
            message: The message to check
            
        Returns:
            True if this handler can handle the message, False otherwise
        """
        return True
