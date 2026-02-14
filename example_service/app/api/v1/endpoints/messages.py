"""Message API endpoints."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, status, Query
from fastapi_building_blocks.api.responses import SuccessResponse

from ....application.commands.message_commands import SendMessageCommand
from ....application.queries.message_queries import (
    GetAllMessagesQuery,
    GetMessagesBySenderQuery,
    GetMessageByIdQuery,
)
from ....application.dtos import SendMessageDTO, MessageDTO
from ...dependencies import MediatorDep

router = APIRouter()


@router.post(
    "/send",
    response_model=SuccessResponse[MessageDTO],
    status_code=status.HTTP_200_OK,
    summary="Send a message to Kafka",
    description="Send a message to Kafka as an integration event. The message will be published to the 'integration-events.message_sent' topic and can be consumed by this service or other services.",
)
async def send_message(
    message_data: SendMessageDTO,
    mediator: MediatorDep,
) -> SuccessResponse[MessageDTO]:
    """
    Send a message to Kafka.
    
    This endpoint demonstrates the integration event pattern:
    1. A command is sent to the mediator
    2. The handler publishes an integration event to Kafka
    3. The integration event can be consumed by this service or other services
    4. Returns the message details
    
    Args:
        message_data: Message data to send
        mediator: Mediator instance for dispatching commands
        
    Returns:
        Success response with message details
    """
    command = SendMessageCommand(
        content=message_data.content,
        sender=message_data.sender,
        metadata=message_data.metadata,
    )
    
    message = await mediator.send(command)
    
    return SuccessResponse.create(
        data=message,
        message="Message sent to Kafka successfully",
    )


@router.get(
    "/",
    response_model=SuccessResponse[List[MessageDTO]],
    status_code=status.HTTP_200_OK,
    summary="Get all messages",
    description="Retrieve all messages from the database with an optional limit.",
)
async def get_all_messages(
    mediator: MediatorDep,
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of messages to return"),
) -> SuccessResponse[List[MessageDTO]]:
    """
    Get all messages.
    
    Args:
        mediator: Mediator instance for dispatching queries
        limit: Maximum number of messages to return
        
    Returns:
        List of messages
    """
    query = GetAllMessagesQuery(limit=limit)
    messages = await mediator.send(query)
    
    message_dtos = [
        MessageDTO(
            message_id=msg.message_id,
            content=msg.content,
            sender=msg.sender,
            timestamp=msg.timestamp,
            metadata=msg.metadata,
        )
        for msg in messages
    ]
    
    return SuccessResponse.create(
        data=message_dtos,
        message=f"Retrieved {len(message_dtos)} messages",
    )


@router.get(
    "/sender/{sender}",
    response_model=SuccessResponse[List[MessageDTO]],
    status_code=status.HTTP_200_OK,
    summary="Get messages by sender",
    description="Retrieve messages from a specific sender.",
)
async def get_messages_by_sender(
    sender: str,
    mediator: MediatorDep,
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of messages to return"),
) -> SuccessResponse[List[MessageDTO]]:
    """
    Get messages by sender.
    
    Args:
        sender: Sender identifier
        mediator: Mediator instance for dispatching queries
        limit: Maximum number of messages to return
        
    Returns:
        List of messages from the sender
    """
    query = GetMessagesBySenderQuery(sender=sender, limit=limit)
    messages = await mediator.send(query)
    
    message_dtos = [
        MessageDTO(
            message_id=msg.message_id,
            content=msg.content,
            sender=msg.sender,
            timestamp=msg.timestamp,
            metadata=msg.metadata,
        )
        for msg in messages
    ]
    
    return SuccessResponse.create(
        data=message_dtos,
        message=f"Retrieved {len(message_dtos)} messages from sender '{sender}'",
    )


@router.get(
    "/{message_id}",
    response_model=SuccessResponse[MessageDTO],
    status_code=status.HTTP_200_OK,
    summary="Get message by ID",
    description="Retrieve a specific message by its ID.",
)
async def get_message_by_id(
    message_id: UUID,
    mediator: MediatorDep,
) -> SuccessResponse[MessageDTO]:
    """
    Get message by ID.
    
    Args:
        message_id: Message ID
        mediator: Mediator instance for dispatching queries
        
    Returns:
        Message details
    """
    query = GetMessageByIdQuery(message_id=message_id)
    message = await mediator.send(query)
    
    if not message:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message with ID {message_id} not found",
        )
    
    message_dto = MessageDTO(
        message_id=message.message_id,
        content=message.content,
        sender=message.sender,
        timestamp=message.timestamp,
        metadata=message.metadata,
    )
    
    return SuccessResponse.create(
        data=message_dto,
        message="Message retrieved successfully",
    )
