"""Application DTOs (Data Transfer Objects)."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi_building_blocks.application import DTO


class UserDTO(DTO):
    """User data transfer object."""
    
    id: UUID
    email: str
    first_name: str
    last_name: str
    bio: Optional[str] = None
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    @property
    def full_name(self) -> str:
        """Get full name."""
        return f"{self.first_name} {self.last_name}"


class CreateUserDTO(DTO):
    """DTO for creating a user."""
    
    email: str
    first_name: str
    last_name: str
    bio: Optional[str] = None


class UpdateUserDTO(DTO):
    """DTO for updating a user."""
    
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
