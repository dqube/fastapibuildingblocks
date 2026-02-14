"""PostgreSQL user repository implementation."""

from typing import Optional
from uuid import UUID

from sqlalchemy import Table, Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from building_blocks.infrastructure import SQLAlchemyRepository, Base

from ...domain.models.user import User, Email, UserProfile
from ...domain.repositories.user_repository import IUserRepository


# SQLAlchemy Table definition
users_table = Table(
    'users',
    Base.metadata,
    Column('id', PGUUID(as_uuid=True), primary_key=True),
    Column('email', String(255), unique=True, nullable=False, index=True),
    Column('first_name', String(100), nullable=False),
    Column('last_name', String(100), nullable=False),
    Column('bio', Text, nullable=True),
    Column('is_active', Boolean, default=True, nullable=False, index=True),
    Column('last_login', DateTime, nullable=True),
    Column('created_at', DateTime, nullable=False),
    Column('updated_at', DateTime, nullable=False),
    extend_existing=True,
)


class PostgreSQLUserRepository(SQLAlchemyRepository[User], IUserRepository):
    """
    PostgreSQL implementation of the user repository.
    
    Extends the generic SQLAlchemyRepository from building blocks,
    providing user-specific querying capabilities.
    """
    
    table = users_table
    
    def __init__(self, session: AsyncSession):
        """
        Initialize the PostgreSQL repository.
        
        Args:
            session: SQLAlchemy async session
        """
        super().__init__(session)
    
    def _row_to_entity(self, row) -> User:
        """
        Convert a database row to a User domain entity.
        
        Args:
            row: SQLAlchemy row result
            
        Returns:
            User domain entity
        """
        return User(
            id=row.id,
            email=Email(value=row.email),
            profile=UserProfile(
                first_name=row.first_name,
                last_name=row.last_name,
                bio=row.bio,
            ),
            is_active=row.is_active,
            last_login=row.last_login,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
    
    def _entity_to_dict(self, entity: User) -> dict:
        """
        Convert a User domain entity to a dictionary for database insertion.
        
        Args:
            entity: User domain entity
            
        Returns:
            Dictionary with database fields
        """
        return {
            'id': entity.id,
            'email': str(entity.email),
            'first_name': entity.profile.first_name,
            'last_name': entity.profile.last_name,
            'bio': entity.profile.bio,
            'is_active': entity.is_active,
            'last_login': entity.last_login,
            'created_at': entity.created_at,
            'updated_at': entity.updated_at,
        }
    
    # User-specific query methods
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email address.
        
        Args:
            email: The user's email address
            
        Returns:
            The user if found, None otherwise
        """
        stmt = select(self.table).where(self.table.c.email == email)
        result = await self._session.execute(stmt)
        row = result.first()
        
        if row:
            return self._row_to_entity(row)
        return None
    
    async def get_active_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """
        Get all active users.
        
        Args:
            skip: Number of users to skip
            limit: Maximum number of users to return
            
        Returns:
            List of active users
        """
        stmt = (
            select(self.table)
            .where(self.table.c.is_active == True)
            .offset(skip)
            .limit(limit)
            .order_by(self.table.c.created_at.desc())
        )
        result = await self._session.execute(stmt)
        rows = result.fetchall()
        
        return [self._row_to_entity(row) for row in rows]
