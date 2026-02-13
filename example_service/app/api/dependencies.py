"""FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_building_blocks.application import IMediator, Mediator

from ..core.database import get_db
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
from ..application.commands.user_commands import (
    CreateUserCommand,
    UpdateUserCommand,
    DeleteUserCommand,
)
from ..application.queries.user_queries import (
    GetUserByIdQuery,
    GetUserByEmailQuery,
    GetAllUsersQuery,
)


# Database session dependency
DatabaseDep = Annotated[AsyncSession, Depends(get_db)]


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


# Mediator dependencies
def get_mediator(
    repository: UserRepositoryDep,
) -> IMediator:
    """
    Get configured mediator instance.
    
    The mediator is configured with all command and query handlers
    registered using factories to ensure proper dependency injection.
    
    Args:
        repository: User repository instance
        
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
    
    return mediator


MediatorDep = Annotated[IMediator, Depends(get_mediator)]
