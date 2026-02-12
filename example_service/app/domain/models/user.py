"""User aggregate root and related value objects."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi_building_blocks.domain import AggregateRoot, ValueObject
from pydantic import EmailStr, Field, field_validator

from ..events.user_events import UserCreatedEvent, UserUpdatedEvent, UserDeletedEvent


class Email(ValueObject):
    """Email value object."""
    
    value: EmailStr
    
    def __str__(self) -> str:
        """String representation."""
        return self.value


class UserProfile(ValueObject):
    """User profile value object."""
    
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    bio: Optional[str] = Field(default=None, max_length=500)
    
    @property
    def full_name(self) -> str:
        """Get full name."""
        return f"{self.first_name} {self.last_name}"


class User(AggregateRoot):
    """
    User aggregate root.
    
    The User is an aggregate root that maintains consistency boundaries
    around user data and encapsulates business rules.
    """
    
    email: Email
    profile: UserProfile
    is_active: bool = Field(default=True)
    last_login: Optional[datetime] = None
    
    @classmethod
    def create(
        cls,
        email: str,
        first_name: str,
        last_name: str,
        bio: Optional[str] = None,
    ) -> "User":
        """
        Create a new user.
        
        Args:
            email: User's email address
            first_name: User's first name
            last_name: User's last name
            bio: Optional user bio
            
        Returns:
            New User instance
        """
        user = cls(
            email=Email(value=email),
            profile=UserProfile(
                first_name=first_name,
                last_name=last_name,
                bio=bio,
            ),
        )
        
        # Add domain event
        user.add_domain_event(
            UserCreatedEvent(
                aggregate_id=user.id,
                email=email,
                full_name=user.profile.full_name,
            )
        )
        
        return user
    
    def update_profile(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        bio: Optional[str] = None,
    ) -> None:
        """
        Update user profile.
        
        Args:
            first_name: New first name
            last_name: New last name
            bio: New bio
        """
        # Create new profile with updated values
        self.profile = UserProfile(
            first_name=first_name or self.profile.first_name,
            last_name=last_name or self.profile.last_name,
            bio=bio if bio is not None else self.profile.bio,
        )
        
        self.update_timestamp()
        
        # Add domain event
        self.add_domain_event(
            UserUpdatedEvent(
                aggregate_id=self.id,
                full_name=self.profile.full_name,
            )
        )
    
    def deactivate(self) -> None:
        """Deactivate the user account."""
        if not self.is_active:
            raise ValueError("User is already deactivated")
        
        self.is_active = False
        self.update_timestamp()
        
        # Add domain event
        self.add_domain_event(
            UserDeletedEvent(
                aggregate_id=self.id,
                email=str(self.email),
            )
        )
    
    def activate(self) -> None:
        """Activate the user account."""
        if self.is_active:
            raise ValueError("User is already active")
        
        self.is_active = True
        self.update_timestamp()
    
    def record_login(self) -> None:
        """Record user login."""
        self.last_login = datetime.utcnow()
        self.update_timestamp()
    
    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v):
        """Validate email field."""
        if isinstance(v, str):
            return Email(value=v)
        return v
