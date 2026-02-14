"""User API endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from building_blocks.api.responses import SuccessResponse, ErrorResponse
from building_blocks.api.exceptions import NotFoundException

from ....application.commands.user_commands import (
    CreateUserCommand,
    UpdateUserCommand,
    DeleteUserCommand,
)
from ....application.queries.user_queries import (
    GetUserByIdQuery,
    GetAllUsersQuery,
)
from ....application.dtos import UserDTO, CreateUserDTO, UpdateUserDTO
from ...dependencies import MediatorDep

router = APIRouter()


@router.post(
    "/",
    response_model=SuccessResponse[UserDTO],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Create a new user with the provided information",
)
async def create_user(
    user_data: CreateUserDTO,
    mediator: MediatorDep,
) -> SuccessResponse[UserDTO]:
    """
    Create a new user.
    
    Args:
        user_data: User creation data
        mediator: Mediator instance for dispatching commands
        
    Returns:
        Success response with created user data
    """
    command = CreateUserCommand(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        bio=user_data.bio,
    )
    
    user = await mediator.send(command)
    
    return SuccessResponse.create(
        data=user,
        message="User created successfully",
    )


@router.get(
    "/{user_id}",
    response_model=SuccessResponse[UserDTO],
    summary="Get user by ID",
    description="Retrieve a user by their unique identifier",
)
async def get_user(
    user_id: UUID,
    mediator: MediatorDep,
) -> SuccessResponse[UserDTO]:
    """
    Get a user by ID.
    
    Args:
        user_id: User's unique identifier
        mediator: Mediator instance for dispatching queries
        
    Returns:
        Success response with user data
        
    Raises:
        NotFoundException: If user not found
    """
    query = GetUserByIdQuery(user_id=user_id)
    user = await mediator.send(query)
    
    if not user:
        raise NotFoundException(message=f"User with ID {user_id} not found")
    
    return SuccessResponse.create(
        data=user,
        message="User retrieved successfully",
    )


@router.get(
    "/",
    response_model=SuccessResponse[List[UserDTO]],
    summary="Get all users",
    description="Retrieve a list of all users with optional pagination",
)
async def get_all_users(
    mediator: MediatorDep,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
) -> SuccessResponse[List[UserDTO]]:
    """
    Get all users.
    
    Args:
        mediator: Mediator instance for dispatching queries
        skip: Number of users to skip (pagination)
        limit: Maximum number of users to return
        active_only: If True, return only active users
        
    Returns:
        Success response with list of users
    """
    query = GetAllUsersQuery(
        skip=skip,
        limit=limit,
        active_only=active_only,
    )
    
    users = await mediator.send(query)
    
    return SuccessResponse.create(
        data=users,
        message=f"Retrieved {len(users)} users",
    )


@router.put(
    "/{user_id}",
    response_model=SuccessResponse[UserDTO],
    summary="Update user",
    description="Update an existing user's information",
)
async def update_user(
    user_id: UUID,
    user_data: UpdateUserDTO,
    mediator: MediatorDep,
) -> SuccessResponse[UserDTO]:
    """
    Update a user.
    
    Args:
        user_id: User's unique identifier
        user_data: User update data
        mediator: Mediator instance for dispatching commands
        
    Returns:
        Success response with updated user data
    """
    command = UpdateUserCommand(
        user_id=user_id,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        bio=user_data.bio,
    )
    
    user = await mediator.send(command)
    
    return SuccessResponse.create(
        data=user,
        message="User updated successfully",
    )


@router.delete(
    "/{user_id}",
    response_model=SuccessResponse[dict],
    summary="Delete user",
    description="Delete a user by their unique identifier",
)
async def delete_user(
    user_id: UUID,
    mediator: MediatorDep,
) -> SuccessResponse[dict]:
    """
    Delete a user.
    
    Args:
        user_id: User's unique identifier
        mediator: Mediator instance for dispatching commands
        
    Returns:
        Success response confirming deletion
    """
    command = DeleteUserCommand(user_id=user_id)
    
    await mediator.send(command)
    
    return SuccessResponse.create(
        data={"deleted": True},
        message="User deleted successfully",
    )
