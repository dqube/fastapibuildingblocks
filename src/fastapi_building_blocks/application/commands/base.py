"""Base Command and CommandHandler classes for CQRS pattern."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel

# Import Request from mediator to make commands compatible
try:
    from ..mediator.base import Request
except ImportError:
    # Fallback if mediator is not available
    Request = BaseModel


TResult = TypeVar("TResult")


class Command(Request, ABC):
    """
    Base class for commands in the CQRS pattern.
    
    Commands represent write operations (create, update, delete) in the system.
    They express the intent to change the system state.
    Commands are compatible with the mediator pattern.
    """
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        arbitrary_types_allowed = True


class CommandHandler(ABC, Generic[TResult]):
    """
    Base class for command handlers.
    
    Command handlers execute commands and coordinate the necessary operations
    to fulfill the command's intent.
    """
    
    @abstractmethod
    async def handle(self, command: Command) -> TResult:
        """
        Handle the command.
        
        Args:
            command: The command to handle
            
        Returns:
            The result of the command execution
        """
        pass
