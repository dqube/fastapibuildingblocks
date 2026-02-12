"""User repository interface."""

from typing import Optional
from uuid import UUID

from fastapi_building_blocks.domain import IRepository
from ..models.user import User


class IUserRepository(IRepository[User]):
    """
    Repository interface for User aggregate.
    
    Extends the base repository with user-specific query methods.
    """
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email address.
        
        Args:
            email: The user's email address
            
        Returns:
            The user if found, None otherwise
        """
        pass
    
    async def get_active_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """
        Get all active users.
        
        Args:
            skip: Number of users to skip
            limit: Maximum number of users to return
            
        Returns:
            List of active users
        """
        pass
