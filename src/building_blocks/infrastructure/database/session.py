"""Database session management."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional


class DatabaseSession(ABC):
    """
    Base class for database session management.
    
    This class provides an abstraction for managing database connections
    and sessions across different database systems.
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize the database session.
        
        Args:
            connection_string: The database connection string
        """
        self.connection_string = connection_string
        self._session = None
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish a connection to the database."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close the database connection."""
        pass
    
    @abstractmethod
    async def get_session(self) -> AsyncGenerator:
        """
        Get a database session.
        
        Yields:
            A database session
        """
        pass
    
    async def __aenter__(self):
        """Enter the async context manager."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context manager."""
        await self.disconnect()
