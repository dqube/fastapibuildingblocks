"""FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends

from ..domain.repositories.user_repository import IUserRepository
from ..infrastructure.repositories.user_repository import InMemoryUserRepository
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


# Repository dependencies
def get_user_repository() -> IUserRepository:
    """
    Get user repository instance.
    
    In a real application, this would return a database-backed repository.
    For simplicity, we're using an in-memory repository.
    """
    # This should be a singleton in production
    return InMemoryUserRepository()


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
