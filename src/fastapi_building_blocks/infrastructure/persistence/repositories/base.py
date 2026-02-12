"""Base Repository implementation for infrastructure layer."""

from typing import Generic, List, Optional, TypeVar
from uuid import UUID

from ....domain.entities.base import BaseEntity
from ....domain.repositories.base import IRepository

T = TypeVar("T", bound=BaseEntity)


class BaseRepository(IRepository[T], Generic[T]):
    """
    Base repository implementation providing common CRUD operations.
    
    This class provides a base implementation for repositories in the
    infrastructure layer. Concrete repositories should inherit from this
    class and provide database-specific implementations.
    """
    
    def __init__(self):
        """Initialize the base repository."""
        self._entities: dict[UUID, T] = {}  # In-memory storage for demonstration
    
    async def get_by_id(self, entity_id: UUID) -> Optional[T]:
        """
        Get an entity by its ID.
        
        Args:
            entity_id: The ID of the entity
            
        Returns:
            The entity if found, None otherwise
        """
        return self._entities.get(entity_id)
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """
        Get all entities with pagination.
        
        Args:
            skip: Number of entities to skip
            limit: Maximum number of entities to return
            
        Returns:
            List of entities
        """
        all_entities = list(self._entities.values())
        return all_entities[skip : skip + limit]
    
    async def add(self, entity: T) -> T:
        """
        Add a new entity.
        
        Args:
            entity: The entity to add
            
        Returns:
            The added entity
        """
        self._entities[entity.id] = entity
        return entity
    
    async def update(self, entity: T) -> T:
        """
        Update an existing entity.
        
        Args:
            entity: The entity to update
            
        Returns:
            The updated entity
        """
        entity.update_timestamp()
        self._entities[entity.id] = entity
        return entity
    
    async def delete(self, entity_id: UUID) -> bool:
        """
        Delete an entity by its ID.
        
        Args:
            entity_id: The ID of the entity to delete
            
        Returns:
            True if the entity was deleted, False otherwise
        """
        if entity_id in self._entities:
            del self._entities[entity_id]
            return True
        return False
    
    async def exists(self, entity_id: UUID) -> bool:
        """
        Check if an entity exists by its ID.
        
        Args:
            entity_id: The ID of the entity
            
        Returns:
            True if the entity exists, False otherwise
        """
        return entity_id in self._entities
