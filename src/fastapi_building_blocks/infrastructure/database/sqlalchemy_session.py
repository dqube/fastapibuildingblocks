"""SQLAlchemy database session management."""

from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base

from .session import DatabaseSession


# Create declarative base for SQLAlchemy models
Base = declarative_base()


class SQLAlchemySession(DatabaseSession):
    """
    SQLAlchemy implementation of DatabaseSession.
    
    Provides async database session management for SQLAlchemy,
    supporting PostgreSQL, MySQL, SQL Server, and other databases.
    """
    
    def __init__(
        self,
        connection_string: str,
        echo: bool = False,
        pool_pre_ping: bool = True,
        pool_size: int = 5,
        max_overflow: int = 10,
    ):
        """
        Initialize SQLAlchemy session.
        
        Args:
            connection_string: Database connection string (e.g., postgresql+asyncpg://...)
            echo: Whether to echo SQL statements (for debugging)
            pool_pre_ping: Enable connection health checks
            pool_size: Number of connections to maintain in pool
            max_overflow: Max connections beyond pool_size
        """
        super().__init__(connection_string)
        self.echo = echo
        self.pool_pre_ping = pool_pre_ping
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None
    
    async def connect(self) -> None:
        """Establish connection to the database."""
        if self._engine is None:
            self._engine = create_async_engine(
                self.connection_string,
                echo=self.echo,
                future=True,
                pool_pre_ping=self.pool_pre_ping,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
            )
            
            self._session_factory = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
    
    async def disconnect(self) -> None:
        """Close database connection."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get an async database session.
        
        Yields:
            AsyncSession: SQLAlchemy async session
        """
        if self._session_factory is None:
            await self.connect()
        
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    @property
    def engine(self) -> Optional[AsyncEngine]:
        """Get the SQLAlchemy engine."""
        return self._engine
    
    async def create_tables(self) -> None:
        """
        Create all tables defined in the metadata.
        
        This should typically only be used in development/testing.
        Use migrations (Alembic) in production.
        """
        if self._engine is None:
            await self.connect()
        
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def drop_tables(self) -> None:
        """
        Drop all tables defined in the metadata.
        
        Warning: This will delete all data! Use with caution.
        """
        if self._engine is None:
            await self.connect()
        
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
