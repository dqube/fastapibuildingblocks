"""SQLAlchemy repository base implementation."""

from typing import Generic, List, Optional, TypeVar, Type
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, Table
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.base import BaseEntity
from ....domain.repositories.base import IRepository

T = TypeVar("T", bound=BaseEntity)


class SQLAlchemyRepository(IRepository[T], Generic[T]):
    """
    Generic SQLAlchemy repository implementation.
    
    Provides database-agnostic CRUD operations using SQLAlchemy Core.
    Works with PostgreSQL, MySQL, SQL Server, SQLite, and other databases
    supported by SQLAlchemy.
    
    Subclasses should define:
    - table: SQLAlchemy Table definition
    - _row_to_entity: Method to convert DB row to domain entity
    - _entity_to_dict: Method to convert domain entity to dict for DB
    """
    
    table: Table = None  # Must be overridden by subclasses
    
    def __init__(self, session: AsyncSession):
        """
        Initialize the repository.
        
        Args:
            session: SQLAlchemy async session
        """
        self._session = session
    
    def _row_to_entity(self, row) -> T:
        """
        Convert a database row to a domain entity.
        
        Args:
            row: SQLAlchemy row result
            
        Returns:
            Domain entity
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement _row_to_entity")
    
    def _entity_to_dict(self, entity: T) -> dict:
        """
        Convert a domain entity to a dictionary for database operations.
        
        Args:
            entity: Domain entity
            
        Returns:
            Dictionary with database fields
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement _entity_to_dict")
    
    async def get_by_id(self, entity_id: UUID) -> Optional[T]:
        """
        Get an entity by its ID.
        
        Args:
            entity_id: The ID of the entity
            
        Returns:
            The entity if found, None otherwise
        """
        stmt = select(self.table).where(self.table.c.id == entity_id)
        result = await self._session.execute(stmt)
        row = result.first()
        
        if row:
            return self._row_to_entity(row)
        return None
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """
        Get all entities with pagination.
        
        Args:
            skip: Number of entities to skip
            limit: Maximum number of entities to return
            
        Returns:
            List of entities
        """
        stmt = (
            select(self.table)
            .offset(skip)
            .limit(limit)
            .order_by(self.table.c.created_at.desc())
        )
        result = await self._session.execute(stmt)
        rows = result.fetchall()
        
        return [self._row_to_entity(row) for row in rows]
    
    async def add(self, entity: T) -> T:
        """
        Add a new entity.
        
        Args:
            entity: The entity to add
            
        Returns:
            The added entity
        """
        stmt = self.table.insert().values(**self._entity_to_dict(entity))
        await self._session.execute(stmt)
        await self._session.flush()
        return entity
    
    async def update(self, entity: T) -> T:
        """
        Update an existing entity.
        
        Args:
            entity: The entity to update
            
        Returns:
            The updated entity
        """
        # Update timestamp
        entity.updated_at = datetime.utcnow()
        
        stmt = (
            self.table.update()
            .where(self.table.c.id == entity.id)
            .values(**self._entity_to_dict(entity))
        )
        await self._session.execute(stmt)
        await self._session.flush()
        return entity
    
    async def delete(self, entity_id: UUID) -> bool:
        """
        Delete an entity by its ID.
        
        Args:
            entity_id: The ID of the entity to delete
            
        Returns:
            True if the entity was deleted, False otherwise
        """
        stmt = self.table.delete().where(self.table.c.id == entity_id)
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount > 0
    
    async def exists(self, entity_id: UUID) -> bool:
        """
        Check if an entity exists by its ID.
        
        Args:
            entity_id: The ID of the entity
            
        Returns:
            True if the entity exists, False otherwise
        """
        entity = await self.get_by_id(entity_id)
        return entity is not None
