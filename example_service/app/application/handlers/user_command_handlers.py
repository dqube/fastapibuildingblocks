"""User command handlers."""

from fastapi_building_blocks.application import CommandHandler
from fastapi_building_blocks.api.exceptions import NotFoundException, ConflictException

from ...domain.models.user import User
from ...domain.repositories.user_repository import IUserRepository
from ..commands.user_commands import (
    CreateUserCommand,
    UpdateUserCommand,
    DeleteUserCommand,
)
from ..dtos import UserDTO


class CreateUserCommandHandler(CommandHandler[UserDTO]):
    """Handler for CreateUserCommand."""
    
    def __init__(self, user_repository: IUserRepository):
        """
        Initialize the handler.
        
        Args:
            user_repository: User repository instance
        """
        self.user_repository = user_repository
    
    async def handle(self, command: CreateUserCommand) -> UserDTO:
        """
        Handle the create user command.
        
        Args:
            command: The create user command
            
        Returns:
            Created user DTO
            
        Raises:
            ConflictException: If user with email already exists
        """
        # Check if user already exists
        existing_user = await self.user_repository.get_by_email(command.email)
        if existing_user:
            raise ConflictException(
                message=f"User with email {command.email} already exists"
            )
        
        # Create new user
        user = User.create(
            email=command.email,
            first_name=command.first_name,
            last_name=command.last_name,
            bio=command.bio,
        )
        
        # Save to repository
        user = await self.user_repository.add(user)
        
        # Convert to DTO
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


class UpdateUserCommandHandler(CommandHandler[UserDTO]):
    """Handler for UpdateUserCommand."""
    
    def __init__(self, user_repository: IUserRepository):
        """
        Initialize the handler.
        
        Args:
            user_repository: User repository instance
        """
        self.user_repository = user_repository
    
    async def handle(self, command: UpdateUserCommand) -> UserDTO:
        """
        Handle the update user command.
        
        Args:
            command: The update user command
            
        Returns:
            Updated user DTO
            
        Raises:
            NotFoundException: If user not found
        """
        # Get existing user
        user = await self.user_repository.get_by_id(command.user_id)
        if not user:
            raise NotFoundException(message=f"User with ID {command.user_id} not found")
        
        # Update user profile
        user.update_profile(
            first_name=command.first_name,
            last_name=command.last_name,
            bio=command.bio,
        )
        
        # Save to repository
        user = await self.user_repository.update(user)
        
        # Convert to DTO
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


class DeleteUserCommandHandler(CommandHandler[bool]):
    """Handler for DeleteUserCommand."""
    
    def __init__(self, user_repository: IUserRepository):
        """
        Initialize the handler.
        
        Args:
            user_repository: User repository instance
        """
        self.user_repository = user_repository
    
    async def handle(self, command: DeleteUserCommand) -> bool:
        """
        Handle the delete user command.
        
        Args:
            command: The delete user command
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundException: If user not found
        """
        # Get existing user
        user = await self.user_repository.get_by_id(command.user_id)
        if not user:
            raise NotFoundException(message=f"User with ID {command.user_id} not found")
        
        # Deactivate user (soft delete)
        user.deactivate()
        await self.user_repository.update(user)
        
        # Or hard delete
        # return await self.user_repository.delete(command.user_id)
        
        return True
