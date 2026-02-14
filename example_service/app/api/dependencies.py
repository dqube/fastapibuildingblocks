"""FastAPI dependencies."""

from typing import Annotated, Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_building_blocks.application import IMediator, Mediator
from fastapi_building_blocks.infrastructure.messaging.base import IEventPublisher
from fastapi_building_blocks.infrastructure.messaging import create_event_publisher

from ..core.database import get_db
from ..core.config import kafka_config
from ..domain.repositories.user_repository import IUserRepository
from ..infrastructure.repositories.postgres_user_repository import PostgreSQLUserRepository
from ..application.handlers.user_command_handlers import (
    CreateUserCommandHandler,
    UpdateUserCommandHandler,
    DeleteUserCommandHandler,
)
from ..application.handlers.user_query_handlers import (
    GetUserByIdQueryHandler,
    GetUserByEmailQueryHandler,
    GetAllUsersQueryHandler,
)
from ..application.handlers.message_command_handlers import SendMessageCommandHandler
from ..application.handlers.message_query_handlers import (
    GetAllMessagesQueryHandler,
    GetMessagesBySenderQueryHandler,
    GetMessageByIdQueryHandler,
)
from ..application.commands.user_commands import (
    CreateUserCommand,
    UpdateUserCommand,
    DeleteUserCommand,
)
from ..application.commands.message_commands import SendMessageCommand
from ..application.queries.user_queries import (
    GetUserByIdQuery,
    GetUserByEmailQuery,
    GetAllUsersQuery,
)
from ..application.queries.message_queries import (
    GetAllMessagesQuery,
    GetMessagesBySenderQuery,
    GetMessageByIdQuery,
)
from ..infrastructure.persistence.repositories.message_repository import MessageRepository


# Database session dependency
DatabaseDep = Annotated[AsyncSession, Depends(get_db)]


def get_event_publisher(db: DatabaseDep) -> IEventPublisher:
    """Get event publisher (uses outbox if enabled)."""
    return create_event_publisher(kafka_config, db)


# Repository dependencies
def get_user_repository(db: DatabaseDep) -> IUserRepository:
    """
    Get user repository instance.
    
    Uses PostgreSQL repository with SQLAlchemy session from building blocks.
    
    Args:
        db: Database session
        
    Returns:
        User repository instance
    """
    return PostgreSQLUserRepository(db)


UserRepositoryDep = Annotated[IUserRepository, Depends(get_user_repository)]


def get_message_repository(db: DatabaseDep) -> MessageRepository:
    """
    Get message repository instance.
    
    Args:
        db: Database session
        
    Returns:
        Message repository instance
    """
    return MessageRepository(db)


MessageRepositoryDep = Annotated[MessageRepository, Depends(get_message_repository)]


# Command handler dependencies
def get_create_user_handler(
    repository: UserRepositoryDep,
) -> CreateUserCommandHandler:
    """Get create user command handler."""
    return CreateUserCommandHandler(repository)


def get_update_user_handler(
    repository: UserRepositoryDep,
) -> UpdateUserCommandHandler:
    """Get update user command handler."""
    return UpdateUserCommandHandler(repository)


def get_delete_user_handler(
    repository: UserRepositoryDep,
) -> DeleteUserCommandHandler:
    """Get delete user command handler."""
    return DeleteUserCommandHandler(repository)


CreateUserHandlerDep = Annotated[
    CreateUserCommandHandler, Depends(get_create_user_handler)
]
UpdateUserHandlerDep = Annotated[
    UpdateUserCommandHandler, Depends(get_update_user_handler)
]
DeleteUserHandlerDep = Annotated[
    DeleteUserCommandHandler, Depends(get_delete_user_handler)
]


# Query handler dependencies
def get_user_by_id_handler(
    repository: UserRepositoryDep,
) -> GetUserByIdQueryHandler:
    """Get user by ID query handler."""
    return GetUserByIdQueryHandler(repository)


def get_user_by_email_handler(
    repository: UserRepositoryDep,
) -> GetUserByEmailQueryHandler:
    """Get user by email query handler."""
    return GetUserByEmailQueryHandler(repository)


def get_all_users_handler(
    repository: UserRepositoryDep,
) -> GetAllUsersQueryHandler:
    """Get all users query handler."""
    return GetAllUsersQueryHandler(repository)


GetUserByIdHandlerDep = Annotated[
    GetUserByIdQueryHandler, Depends(get_user_by_id_handler)
]
GetUserByEmailHandlerDep = Annotated[
    GetUserByEmailQueryHandler, Depends(get_user_by_email_handler)
]
GetAllUsersHandlerDep = Annotated[
    GetAllUsersQueryHandler, Depends(get_all_users_handler)
]


EventPublisherDep = Annotated[IEventPublisher, Depends(get_event_publisher)]


# Mediator dependencies
def get_mediator(
    repository: UserRepositoryDep,
    message_repository: MessageRepositoryDep,
    event_publisher: EventPublisherDep,
    db: DatabaseDep,
) -> IMediator:
    """
    Get configured mediator instance.
    
    The mediator is configured with all command and query handlers
    registered using factories to ensure proper dependency injection.
    
    Args:
        repository: User repository instance
        message_repository: Message repository instance
        event_publisher: Event publisher (uses outbox if enabled)
        db: Database session
        
    Returns:
        Configured mediator instance
    """
    mediator = Mediator()
    
    # Register command handlers
    mediator.register_handler_factory(
        CreateUserCommand,
        lambda: CreateUserCommandHandler(repository)
    )
    mediator.register_handler_factory(
        UpdateUserCommand,
        lambda: UpdateUserCommandHandler(repository)
    )
    mediator.register_handler_factory(
        DeleteUserCommand,
        lambda: DeleteUserCommandHandler(repository)
    )
    
    # Register message command handler (with session-scoped publisher)
    mediator.register_handler_factory(
        SendMessageCommand,
        lambda: SendMessageCommandHandler(event_publisher, db)
    )
    
    # Register query handlers
    mediator.register_handler_factory(
        GetUserByIdQuery,
        lambda: GetUserByIdQueryHandler(repository)
    )
    mediator.register_handler_factory(
        GetUserByEmailQuery,
        lambda: GetUserByEmailQueryHandler(repository)
    )
    mediator.register_handler_factory(
        GetAllUsersQuery,
        lambda: GetAllUsersQueryHandler(repository)
    )
    
    # Register message query handlers
    mediator.register_handler_factory(
        GetAllMessagesQuery,
        lambda: GetAllMessagesQueryHandler(message_repository)
    )
    mediator.register_handler_factory(
        GetMessagesBySenderQuery,
        lambda: GetMessagesBySenderQueryHandler(message_repository)
    )
    mediator.register_handler_factory(
        GetMessageByIdQuery,
        lambda: GetMessageByIdQueryHandler(message_repository)
    )
    
    return mediator


MediatorDep = Annotated[IMediator, Depends(get_mediator)]
