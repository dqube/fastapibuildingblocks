"""FastAPI dependency for mediator pattern."""

from typing import Annotated

from fastapi import Depends

from ...application.mediator import IMediator, Mediator


def get_mediator() -> IMediator:
    """
    Get mediator instance.
    
    In production, this should return a singleton mediator instance
    that has all handlers pre-registered. This can be done during
    application startup.
    
    Returns:
        Mediator instance
    """
    # Return a mediator instance
    # In practice, this would be a singleton configured at startup
    return Mediator()


# Type alias for mediator dependency injection
MediatorDep = Annotated[IMediator, Depends(get_mediator)]
