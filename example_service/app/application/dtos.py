"""Application DTOs (Data Transfer Objects)."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field, EmailStr
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
    
    email: EmailStr = Field(..., examples=["user@example.com"], description="User's email address")
    first_name: str = Field(..., min_length=1, max_length=50, examples=["John"], description="User's first name")
    last_name: str = Field(..., min_length=1, max_length=50, examples=["Doe"], description="User's last name")
    bio: Optional[str] = Field(None, max_length=500, examples=["Software developer interested in DDD"], description="User's biography")


class UpdateUserDTO(DTO):
    """DTO for updating a user."""
    
    first_name: Optional[str] = Field(None, min_length=1, max_length=50, examples=["Jane"], description="User's first name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=50, examples=["Smith"], description="User's last name")
    bio: Optional[str] = Field(None, max_length=500, examples=["Updated bio"], description="User's biography")
