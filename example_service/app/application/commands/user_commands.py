"""User-related commands."""

from typing import Optional
from uuid import UUID

from building_blocks.application import Command


class CreateUserCommand(Command):
    """Command to create a new user."""
    
    email: str
    first_name: str
    last_name: str
    bio: Optional[str] = None


class UpdateUserCommand(Command):
    """Command to update an existing user."""
    
    user_id: UUID
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None


class DeleteUserCommand(Command):
    """Command to delete a user."""
    
    user_id: UUID
