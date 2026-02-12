"""In-memory user repository implementation."""

from typing import Optional
from uuid import UUID

from fastapi_building_blocks.infrastructure import BaseRepository

from ...domain.models.user import User
from ...domain.repositories.user_repository import IUserRepository


class InMemoryUserRepository(BaseRepository[User], IUserRepository):
    """
    In-memory implementation of the user repository.
    
    This is a simple implementation for demonstration purposes.
    In production, you would use a database-backed implementation.
    """
    
    def __init__(self):
        """Initialize the in-memory repository."""
        super().__init__()
        self._email_index: dict[str, UUID] = {}
    
    async def add(self, entity: User) -> User:
        """
        Add a new user.
        
        Args:
            entity: The user to add
            
        Returns:
            The added user
        """
        user = await super().add(entity)
        # Update email index
        self._email_index[str(user.email)] = user.id
        return user
    
    async def update(self, entity: User) -> User:
        """
        Update an existing user.
        
        Args:
            entity: The user to update
            
        Returns:
            The updated user
        """
        # Update email index if email changed
        old_user = self._entities.get(entity.id)
        if old_user and str(old_user.email) != str(entity.email):
            # Remove old email from index
            self._email_index.pop(str(old_user.email), None)
            # Add new email to index
            self._email_index[str(entity.email)] = entity.id
        
        return await super().update(entity)
    
    async def delete(self, entity_id: UUID) -> bool:
        """
        Delete a user by ID.
        
        Args:
            entity_id: The ID of the user to delete
            
        Returns:
            True if deleted, False otherwise
        """
        user = self._entities.get(entity_id)
        if user:
            # Remove from email index
            self._email_index.pop(str(user.email), None)
        
        return await super().delete(entity_id)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email address.
        
        Args:
            email: The user's email address
            
        Returns:
            The user if found, None otherwise
        """
        user_id = self._email_index.get(email)
        if user_id:
            return await self.get_by_id(user_id)
        return None
    
    async def get_active_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """
        Get all active users.
        
        Args:
            skip: Number of users to skip
            limit: Maximum number of users to return
            
        Returns:
            List of active users
        """
        active_users = [user for user in self._entities.values() if user.is_active]
        return active_users[skip : skip + limit]
