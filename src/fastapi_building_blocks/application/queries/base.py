"""Base Query and QueryHandler classes for CQRS pattern."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel


TResult = TypeVar("TResult")


class Query(BaseModel, ABC):
    """
    Base class for queries in the CQRS pattern.
    
    Queries represent read operations in the system. They request data
    without causing any side effects or state changes.
    """
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        arbitrary_types_allowed = True


class QueryHandler(ABC, Generic[TResult]):
    """
    Base class for query handlers.
    
    Query handlers execute queries and return the requested data.
    """
    
    @abstractmethod
    async def handle(self, query: Query) -> TResult:
        """
        Handle the query.
        
        Args:
            query: The query to handle
            
        Returns:
            The result of the query execution
        """
        pass
