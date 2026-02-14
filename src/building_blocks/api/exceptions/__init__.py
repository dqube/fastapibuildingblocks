"""API exception classes."""

from .base import (
    APIException,
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
)
from .problem_details import (
    ProblemDetails,
    ValidationProblemDetails,
    create_problem_details,
)
from .handler import (
    GlobalExceptionHandler,
    setup_exception_handlers,
)

__all__ = [
    # Base exceptions
    "APIException",
    "NotFoundException",
    "BadRequestException",
    "UnauthorizedException",
    "ForbiddenException",
    "ConflictException",
    # Problem Details (RFC 7807)
    "ProblemDetails",
    "ValidationProblemDetails",
    "create_problem_details",
    # Global exception handler
    "GlobalExceptionHandler",
    "setup_exception_handlers",
]
