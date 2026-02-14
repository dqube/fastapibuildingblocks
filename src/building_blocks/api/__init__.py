"""
API Layer

The HTTP interface layer containing FastAPI utilities for dependencies,
middleware, responses, and exception handling.
"""

from .dependencies.base import Dependency
from .middleware.base import BaseMiddleware
from .responses.base import BaseResponse, SuccessResponse, ErrorResponse
from .exceptions.base import APIException, NotFoundException, BadRequestException

__all__ = [
    "Dependency",
    "BaseMiddleware",
    "BaseResponse",
    "SuccessResponse",
    "ErrorResponse",
    "APIException",
    "NotFoundException",
    "BadRequestException",
]
