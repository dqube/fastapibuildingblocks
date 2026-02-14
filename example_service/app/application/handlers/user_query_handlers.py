"""User query handlers."""

from typing import List, Optional

from building_blocks.application import QueryHandler
from building_blocks.api.exceptions import NotFoundException

from ...domain.repositories.user_repository import IUserRepository
from ..queries.user_queries import (
    GetUserByIdQuery,
    GetUserByEmailQuery,
    GetAllUsersQuery,
    GetActiveUsersQuery,
)
from ..dtos import UserDTO


class GetUserByIdQueryHandler(QueryHandler[Optional[UserDTO]]):
    """Handler for GetUserByIdQuery."""
    
    def __init__(self, user_repository: IUserRepository):
        """
        Initialize the handler.
        
        Args:
            user_repository: User repository instance
        """
        self.user_repository = user_repository
    
    async def handle(self, query: GetUserByIdQuery) -> Optional[UserDTO]:
        """
        Handle the get user by ID query.
        
        Args:
            query: The get user by ID query
            
        Returns:
            User DTO if found, None otherwise
        """
        user = await self.user_repository.get_by_id(query.user_id)
        
        if not user:
            return None
        
        return UserDTO(
            id=user.id,
            email=str(user.email),
            first_name=user.profile.first_name,
            last_name=user.profile.last_name,
            bio=user.profile.bio,
            is_active=user.is_active,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )


class GetUserByEmailQueryHandler(QueryHandler[Optional[UserDTO]]):
    """Handler for GetUserByEmailQuery."""
    
    def __init__(self, user_repository: IUserRepository):
        """
        Initialize the handler.
        
        Args:
            user_repository: User repository instance
        """
        self.user_repository = user_repository
    
    async def handle(self, query: GetUserByEmailQuery) -> Optional[UserDTO]:
        """
        Handle the get user by email query.
        
        Args:
            query: The get user by email query
            
        Returns:
            User DTO if found, None otherwise
        """
        user = await self.user_repository.get_by_email(query.email)
        
        if not user:
            return None
        
        return UserDTO(
            id=user.id,
            email=str(user.email),
            first_name=user.profile.first_name,
            last_name=user.profile.last_name,
            bio=user.profile.bio,
            is_active=user.is_active,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )


class GetAllUsersQueryHandler(QueryHandler[List[UserDTO]]):
    """Handler for GetAllUsersQuery."""
    
    def __init__(self, user_repository: IUserRepository):
        """
        Initialize the handler.
        
        Args:
            user_repository: User repository instance
        """
        self.user_repository = user_repository
    
    async def handle(self, query: GetAllUsersQuery) -> List[UserDTO]:
        """
        Handle the get all users query.
        
        Args:
            query: The get all users query
            
        Returns:
            List of user DTOs
        """
        if query.active_only:
            users = await self.user_repository.get_active_users(
                skip=query.skip,
                limit=query.limit,
            )
        else:
            users = await self.user_repository.get_all(
                skip=query.skip,
                limit=query.limit,
            )
        
        return [
            UserDTO(
                id=user.id,
                email=str(user.email),
                first_name=user.profile.first_name,
                last_name=user.profile.last_name,
                bio=user.profile.bio,
                is_active=user.is_active,
                last_login=user.last_login,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
            for user in users
        ]
