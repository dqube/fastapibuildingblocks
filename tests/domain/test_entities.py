"""Sample test for entity base class."""

import pytest
from uuid import uuid4

from building_blocks.domain.entities.base import BaseEntity


class User(BaseEntity):
    """Sample user entity for testing."""
    name: str
    email: str


def test_entity_creation():
    """Test creating an entity."""
    user = User(name="John Doe", email="john@example.com")
    
    assert user.name == "John Doe"
    assert user.email == "john@example.com"
    assert user.id is not None
    assert user.created_at is not None
    assert user.updated_at is not None


def test_entity_equality():
    """Test entity equality based on ID."""
    user_id = uuid4()
    user1 = User(id=user_id, name="John Doe", email="john@example.com")
    user2 = User(id=user_id, name="Jane Doe", email="jane@example.com")
    user3 = User(name="John Doe", email="john@example.com")
    
    assert user1 == user2  # Same ID, so equal
    assert user1 != user3  # Different IDs
