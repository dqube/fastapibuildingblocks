"""Base dependency class for FastAPI dependency injection."""

from abc import ABC
from typing import Any


class Dependency(ABC):
    """
    Base class for FastAPI dependencies.
    
    Dependencies are used for dependency injection in FastAPI endpoints.
    They can provide database sessions, authentication, services, etc.
    """
    
    async def __call__(self) -> Any:
        """
        Make the dependency callable.
        
        Returns:
            The dependency instance or value
        """
        return self
