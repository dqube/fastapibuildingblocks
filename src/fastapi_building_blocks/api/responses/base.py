"""Base response classes for standardized API responses."""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """
    Base class for all API responses.
    
    Provides a standardized response structure for all API endpoints.
    """
    
    success: bool = Field(description="Whether the request was successful")
    message: Optional[str] = Field(default=None, description="Response message")
    data: Optional[T] = Field(default=None, description="Response data")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class SuccessResponse(BaseResponse[T], Generic[T]):
    """
    Standard success response.
    
    Used when an API operation completes successfully.
    """
    
    success: bool = Field(default=True, description="Always True for success responses")
    
    @classmethod
    def create(cls, data: T, message: str = "Success") -> "SuccessResponse[T]":
        """
        Create a success response.
        
        Args:
            data: The response data
            message: The success message
            
        Returns:
            Success response instance
        """
        return cls(success=True, message=message, data=data)


class ErrorResponse(BaseResponse[None]):
    """
    Standard error response.
    
    Used when an API operation fails.
    """
    
    success: bool = Field(default=False, description="Always False for error responses")
    error_code: Optional[str] = Field(default=None, description="Error code")
    
    @classmethod
    def create(cls, message: str, error_code: Optional[str] = None) -> "ErrorResponse":
        """
        Create an error response.
        
        Args:
            message: The error message
            error_code: Optional error code
            
        Returns:
            Error response instance
        """
        return cls(success=False, message=message, error_code=error_code)
