"""Database configuration and session management."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_building_blocks.infrastructure import SQLAlchemySession

from .config import settings

# Create SQLAlchemy session using building blocks infrastructure
db_session = SQLAlchemySession(
    connection_string=settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session.
    
    Yields:
        AsyncSession: Database session
    """
    async for session in db_session.get_session():
        yield session


async def init_db():
    """Initialize database connection."""
    await db_session.connect()


async def close_db():
    """Close database connection."""
    await db_session.disconnect()


def get_session_factory():
    """
    Get the SQLAlchemy session factory.
    
    This is used by background workers (like OutboxRelay) that need
    to create their own database sessions.
    
    Returns:
        The async session factory
    """
    return db_session.get_session_factory()
