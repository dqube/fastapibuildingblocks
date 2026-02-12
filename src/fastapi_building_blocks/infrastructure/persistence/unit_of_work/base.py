"""Base Unit of Work interface for transaction management."""

from abc import ABC, abstractmethod


class IUnitOfWork(ABC):
    """
    Unit of Work interface for transaction management.
    
    The Unit of Work pattern maintains a list of objects affected by a business
    transaction and coordinates the writing out of changes and the resolution
    of concurrency problems.
    """
    
    @abstractmethod
    async def begin(self) -> None:
        """Begin a new transaction."""
        pass
    
    @abstractmethod
    async def commit(self) -> None:
        """Commit the current transaction."""
        pass
    
    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        pass
    
    @abstractmethod
    async def __aenter__(self):
        """Enter the async context manager."""
        await self.begin()
        return self
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context manager."""
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()
