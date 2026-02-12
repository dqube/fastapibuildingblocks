"""Base ValueObject class for domain value objects."""

from abc import ABC
from typing import Any

from pydantic import BaseModel


class ValueObject(BaseModel, ABC):
    """
    Base class for all value objects.
    
    A value object is an immutable object that is defined by its attributes.
    Value objects have no identity - two value objects with the same attributes
    are considered equal.
    """
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Makes the value object immutable
        validate_assignment = True
        arbitrary_types_allowed = True
    
    def __eq__(self, other: Any) -> bool:
        """
        Value objects are equal if all their attributes are equal.
        
        Args:
            other: The other object to compare with
            
        Returns:
            True if all attributes are equal, False otherwise
        """
        if not isinstance(other, self.__class__):
            return False
        return self.model_dump() == other.model_dump()
    
    def __hash__(self) -> int:
        """
        Hash based on all attributes.
        
        Returns:
            Hash of all attributes
        """
        return hash(tuple(sorted(self.model_dump().items())))
