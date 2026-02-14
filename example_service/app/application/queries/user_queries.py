"""User-related queries."""

from typing import Optional
from uuid import UUID

from building_blocks.application import Query


class GetUserByIdQuery(Query):
    """Query to get a user by ID."""
    
    user_id: UUID


class GetUserByEmailQuery(Query):
    """Query to get a user by email."""
    
    email: str


class GetAllUsersQuery(Query):
    """Query to get all users."""
    
    skip: int = 0
    limit: int = 100
    active_only: bool = False


class GetActiveUsersQuery(Query):
    """Query to get active users only."""
    
    skip: int = 0
    limit: int = 100
