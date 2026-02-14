"""Base exception classes for API errors."""

from typing import Any, Optional

from fastapi import HTTPException, status


class APIException(HTTPException):
    """
    Base class for API exceptions.
    
    All custom API exceptions should inherit from this class.
    """
    
    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: Optional[str] = None,
        headers: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize the API exception.
        
        Args:
            status_code: HTTP status code
            message: Error message
            error_code: Optional error code
            headers: Optional HTTP headers
        """
        self.error_code = error_code
        super().__init__(status_code=status_code, detail=message, headers=headers)


class NotFoundException(APIException):
    """
    Exception raised when a resource is not found.
    
    Maps to HTTP 404 Not Found.
    """
    
    def __init__(
        self,
        message: str = "Resource not found",
        error_code: str = "NOT_FOUND",
    ):
        """
        Initialize the not found exception.
        
        Args:
            message: Error message
            error_code: Error code
        """
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error_code=error_code,
        )


class BadRequestException(APIException):
    """
    Exception raised when the request is invalid.
    
    Maps to HTTP 400 Bad Request.
    """
    
    def __init__(
        self,
        message: str = "Bad request",
        error_code: str = "BAD_REQUEST",
    ):
        """
        Initialize the bad request exception.
        
        Args:
            message: Error message
            error_code: Error code
        """
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
            error_code=error_code,
        )


class UnauthorizedException(APIException):
    """
    Exception raised when authentication fails.
    
    Maps to HTTP 401 Unauthorized.
    """
    
    def __init__(
        self,
        message: str = "Unauthorized",
        error_code: str = "UNAUTHORIZED",
    ):
        """
        Initialize the unauthorized exception.
        
        Args:
            message: Error message
            error_code: Error code
        """
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            error_code=error_code,
        )


class ForbiddenException(APIException):
    """
    Exception raised when access is forbidden.
    
    Maps to HTTP 403 Forbidden.
    """
    
    def __init__(
        self,
        message: str = "Forbidden",
        error_code: str = "FORBIDDEN",
    ):
        """
        Initialize the forbidden exception.
        
        Args:
            message: Error message
            error_code: Error code
        """
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            error_code=error_code,
        )


class ConflictException(APIException):
    """
    Exception raised when there's a conflict with the current state.
    
    Maps to HTTP 409 Conflict.
    """
    
    def __init__(
        self,
        message: str = "Conflict",
        error_code: str = "CONFLICT",
    ):
        """
        Initialize the conflict exception.
        
        Args:
            message: Error message
            error_code: Error code
        """
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            error_code=error_code,
        )
