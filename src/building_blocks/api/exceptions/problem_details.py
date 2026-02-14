"""
ProblemDetails implementation following RFC 7807.

This module provides standardized error responses compatible with .NET's ProblemDetails.
"""

from typing import Any, Optional
from pydantic import BaseModel, Field


class ProblemDetails(BaseModel):
    """
    RFC 7807 Problem Details for HTTP APIs.
    
    This class represents a standardized way to carry machine-readable details
    of errors in HTTP responses, similar to .NET's ProblemDetails.
    
    See: https://datatracker.ietf.org/doc/html/rfc7807
    
    Example:
        ```python
        problem = ProblemDetails(
            type="https://api.example.com/errors/validation-error",
            title="Validation Error",
            status=400,
            detail="The email field is required",
            instance="/api/users",
            errors={"email": ["The email field is required"]}
        )
        ```
    """
    
    type: str = Field(
        default="about:blank",
        description="A URI reference that identifies the problem type"
    )
    
    title: str = Field(
        description="A short, human-readable summary of the problem type"
    )
    
    status: int = Field(
        description="The HTTP status code"
    )
    
    detail: Optional[str] = Field(
        default=None,
        description="A human-readable explanation specific to this occurrence"
    )
    
    instance: Optional[str] = Field(
        default=None,
        description="A URI reference that identifies the specific occurrence"
    )
    
    # Extension members (similar to .NET)
    trace_id: Optional[str] = Field(
        default=None,
        description="The correlation/trace ID for tracking"
    )
    
    errors: Optional[dict[str, list[str]]] = Field(
        default=None,
        description="Validation errors (field -> list of error messages)"
    )
    
    extensions: Optional[dict[str, Any]] = Field(
        default=None,
        description="Additional custom properties"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "type": "https://tools.ietf.org/html/rfc7231#section-6.5.1",
                "title": "Bad Request",
                "status": 400,
                "detail": "Validation failed for one or more fields",
                "instance": "/api/users",
                "trace_id": "0HMVB8799T123",
                "errors": {
                    "email": ["The email field is required"],
                    "age": ["Must be greater than 0"]
                }
            }
        }


class ValidationProblemDetails(ProblemDetails):
    """
    Specialized ProblemDetails for validation errors.
    
    Similar to .NET's ValidationProblemDetails.
    """
    
    def __init__(
        self,
        errors: dict[str, list[str]],
        detail: Optional[str] = None,
        instance: Optional[str] = None,
        trace_id: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize validation problem details.
        
        Args:
            errors: Dictionary of field names to error messages
            detail: Optional detail message
            instance: Optional instance URI
            trace_id: Optional trace/correlation ID
            **kwargs: Additional fields
        """
        super().__init__(
            type=kwargs.get("type", "https://tools.ietf.org/html/rfc7231#section-6.5.1"),
            title=kwargs.get("title", "One or more validation errors occurred"),
            status=kwargs.get("status", 400),
            detail=detail or "Validation failed for the request",
            instance=instance,
            trace_id=trace_id,
            errors=errors,
            **{k: v for k, v in kwargs.items() if k not in ["type", "title", "status"]}
        )


def create_problem_details(
    status: int,
    title: str,
    detail: Optional[str] = None,
    type_uri: Optional[str] = None,
    instance: Optional[str] = None,
    trace_id: Optional[str] = None,
    errors: Optional[dict[str, list[str]]] = None,
    **extensions
) -> ProblemDetails:
    """
    Factory function to create ProblemDetails instances.
    
    Args:
        status: HTTP status code
        title: Error title
        detail: Detailed error message
        type_uri: Problem type URI
        instance: Request instance URI
        trace_id: Trace/correlation ID
        errors: Validation errors
        **extensions: Additional custom fields
    
    Returns:
        ProblemDetails instance
    """
    # Default type URIs based on status code
    default_types = {
        400: "https://tools.ietf.org/html/rfc7231#section-6.5.1",
        401: "https://tools.ietf.org/html/rfc7235#section-3.1",
        403: "https://tools.ietf.org/html/rfc7231#section-6.5.3",
        404: "https://tools.ietf.org/html/rfc7231#section-6.5.4",
        409: "https://tools.ietf.org/html/rfc7231#section-6.5.8",
        422: "https://tools.ietf.org/html/rfc4918#section-11.2",
        500: "https://tools.ietf.org/html/rfc7231#section-6.6.1",
    }
    
    return ProblemDetails(
        type=type_uri or default_types.get(status, "about:blank"),
        title=title,
        status=status,
        detail=detail,
        instance=instance,
        trace_id=trace_id,
        errors=errors,
        extensions=extensions if extensions else None
    )
