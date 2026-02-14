"""
Global exception handler for FastAPI applications.

This module provides centralized exception handling similar to .NET's
GlobalExceptionHandler with ProblemDetails responses.
"""

import logging
import traceback
from typing import Union, Callable, Any
from uuid import uuid4

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .problem_details import ProblemDetails, ValidationProblemDetails, create_problem_details
from .base import APIException


logger = logging.getLogger(__name__)


class GlobalExceptionHandler:
    """
    Global exception handler for FastAPI applications.
    
    Provides centralized exception handling with RFC 7807 ProblemDetails responses,
    similar to .NET's GlobalExceptionHandler.
    
    Features:
    - Automatic conversion of exceptions to ProblemDetails
    - Logging with trace IDs
    - Validation error formatting
    - Custom exception handlers
    - Observability integration (trace IDs)
    
    Example:
        ```python
        from fastapi import FastAPI
        from building_blocks.api.exceptions import GlobalExceptionHandler
        
        app = FastAPI()
        
        # Register global handler
        handler = GlobalExceptionHandler(
            app=app,
            include_stack_trace=False,  # True for development
            log_errors=True
        )
        
        # Or manually
        handler.register_handlers()
        ```
    """
    
    def __init__(
        self,
        app: FastAPI,
        include_stack_trace: bool = False,
        log_errors: bool = True,
        include_request_details: bool = False,
        custom_handlers: dict[type[Exception], Callable] = None
    ):
        """
        Initialize the global exception handler.
        
        Args:
            app: FastAPI application instance
            include_stack_trace: Include stack traces in responses (for development)
            log_errors: Log exceptions
            include_request_details: Include request details in error response
            custom_handlers: Dictionary of exception types to custom handler functions
        """
        self.app = app
        self.include_stack_trace = include_stack_trace
        self.log_errors = log_errors
        self.include_request_details = include_request_details
        self.custom_handlers = custom_handlers or {}
        
        # Register all handlers
        self.register_handlers()
    
    def register_handlers(self):
        """Register all exception handlers with the FastAPI app."""
        # API exceptions (custom)
        self.app.add_exception_handler(APIException, self.handle_api_exception)
        
        # HTTP exceptions
        self.app.add_exception_handler(HTTPException, self.handle_http_exception)
        self.app.add_exception_handler(StarletteHTTPException, self.handle_http_exception)
        
        # Validation exceptions
        self.app.add_exception_handler(RequestValidationError, self.handle_validation_exception)
        self.app.add_exception_handler(ValidationError, self.handle_pydantic_validation_exception)
        
        # Generic exceptions (catch-all)
        self.app.add_exception_handler(Exception, self.handle_generic_exception)
    
    async def handle_api_exception(
        self,
        request: Request,
        exc: APIException
    ) -> JSONResponse:
        """
        Handle custom API exceptions.
        
        Args:
            request: FastAPI request
            exc: APIException instance
            
        Returns:
            JSONResponse with ProblemDetails
        """
        trace_id = self._get_trace_id(request)
        
        problem = create_problem_details(
            status=exc.status_code,
            title=self._get_status_title(exc.status_code),
            detail=exc.detail,
            instance=str(request.url.path),
            trace_id=trace_id,
            error_code=getattr(exc, 'error_code', None)
        )
        
        if self.log_errors:
            logger.error(
                f"API Exception: {exc.detail}",
                extra={
                    "trace_id": trace_id,
                    "status_code": exc.status_code,
                    "error_code": getattr(exc, 'error_code', None),
                    "path": request.url.path
                }
            )
        
        return self._create_response(problem, exc.headers)
    
    async def handle_http_exception(
        self,
        request: Request,
        exc: Union[HTTPException, StarletteHTTPException]
    ) -> JSONResponse:
        """
        Handle FastAPI/Starlette HTTP exceptions.
        
        Args:
            request: FastAPI request
            exc: HTTPException instance
            
        Returns:
            JSONResponse with ProblemDetails
        """
        trace_id = self._get_trace_id(request)
        
        problem = create_problem_details(
            status=exc.status_code,
            title=self._get_status_title(exc.status_code),
            detail=str(exc.detail),
            instance=str(request.url.path),
            trace_id=trace_id
        )
        
        if self.log_errors:
            logger.warning(
                f"HTTP Exception: {exc.detail}",
                extra={
                    "trace_id": trace_id,
                    "status_code": exc.status_code,
                    "path": request.url.path
                }
            )
        
        return self._create_response(problem, getattr(exc, 'headers', None))
    
    async def handle_validation_exception(
        self,
        request: Request,
        exc: RequestValidationError
    ) -> JSONResponse:
        """
        Handle FastAPI request validation errors.
        
        Args:
            request: FastAPI request
            exc: RequestValidationError instance
            
        Returns:
            JSONResponse with ValidationProblemDetails
        """
        trace_id = self._get_trace_id(request)
        
        # Format validation errors
        errors = self._format_validation_errors(exc.errors())
        
        problem = ValidationProblemDetails(
            errors=errors,
            detail="One or more validation errors occurred",
            instance=str(request.url.path),
            trace_id=trace_id
        )
        
        if self.log_errors:
            logger.warning(
                f"Validation error: {len(errors)} field(s) failed validation",
                extra={
                    "trace_id": trace_id,
                    "path": request.url.path,
                    "errors": errors
                }
            )
        
        return self._create_response(problem)
    
    async def handle_pydantic_validation_exception(
        self,
        request: Request,
        exc: ValidationError
    ) -> JSONResponse:
        """
        Handle Pydantic validation errors.
        
        Args:
            request: FastAPI request
            exc: ValidationError instance
            
        Returns:
            JSONResponse with ValidationProblemDetails
        """
        trace_id = self._get_trace_id(request)
        
        # Format validation errors
        errors = self._format_validation_errors(exc.errors())
        
        problem = ValidationProblemDetails(
            errors=errors,
            detail="One or more validation errors occurred",
            instance=str(request.url.path),
            trace_id=trace_id
        )
        
        if self.log_errors:
            logger.warning(
                f"Pydantic validation error: {len(errors)} field(s) failed validation",
                extra={
                    "trace_id": trace_id,
                    "path": request.url.path,
                    "errors": errors
                }
            )
        
        return self._create_response(problem)
    
    async def handle_generic_exception(
        self,
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        """
        Handle all other unhandled exceptions.
        
        Args:
            request: FastAPI request
            exc: Exception instance
            
        Returns:
            JSONResponse with ProblemDetails
        """
        # Check if custom handler exists
        exc_type = type(exc)
        if exc_type in self.custom_handlers:
            return await self.custom_handlers[exc_type](request, exc)
        
        trace_id = self._get_trace_id(request)
        
        # Log the full exception
        if self.log_errors:
            logger.exception(
                f"Unhandled exception: {str(exc)}",
                extra={
                    "trace_id": trace_id,
                    "path": request.url.path,
                    "exception_type": exc_type.__name__
                },
                exc_info=exc
            )
        
        # Create problem details
        extensions = {}
        if self.include_stack_trace:
            extensions["stack_trace"] = traceback.format_exc()
        
        if self.include_request_details:
            extensions["request"] = {
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers)
            }
        
        problem = create_problem_details(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            title="Internal Server Error",
            detail="An unexpected error occurred while processing your request",
            instance=str(request.url.path),
            trace_id=trace_id,
            **extensions
        )
        
        return self._create_response(problem)
    
    def _create_response(
        self,
        problem: ProblemDetails,
        headers: dict[str, Any] = None
    ) -> JSONResponse:
        """
        Create JSONResponse from ProblemDetails.
        
        Args:
            problem: ProblemDetails instance
            headers: Optional HTTP headers
            
        Returns:
            JSONResponse
        """
        response_headers = headers or {}
        response_headers["Content-Type"] = "application/problem+json"
        
        return JSONResponse(
            status_code=problem.status,
            content=problem.model_dump(exclude_none=True),
            headers=response_headers
        )
    
    def _get_trace_id(self, request: Request) -> str:
        """
        Get or generate trace ID for the request.
        
        Args:
            request: FastAPI request
            
        Returns:
            Trace ID string
        """
        # Try to get from request state (set by observability middleware)
        if hasattr(request.state, "trace_id"):
            return request.state.trace_id
        
        # Try headers
        trace_id = (
            request.headers.get("x-trace-id") or
            request.headers.get("x-request-id") or
            request.headers.get("x-correlation-id")
        )
        
        if trace_id:
            return trace_id
        
        # Generate new one
        return str(uuid4())
    
    def _get_status_title(self, status_code: int) -> str:
        """
        Get human-readable title for HTTP status code.
        
        Args:
            status_code: HTTP status code
            
        Returns:
            Status title
        """
        titles = {
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            405: "Method Not Allowed",
            409: "Conflict",
            422: "Unprocessable Entity",
            429: "Too Many Requests",
            500: "Internal Server Error",
            502: "Bad Gateway",
            503: "Service Unavailable",
            504: "Gateway Timeout"
        }
        return titles.get(status_code, "Error")
    
    def _format_validation_errors(
        self,
        errors: list[dict]
    ) -> dict[str, list[str]]:
        """
        Format Pydantic validation errors to ProblemDetails format.
        
        Args:
            errors: List of Pydantic error dicts
            
        Returns:
            Dictionary of field names to error messages
        """
        formatted_errors: dict[str, list[str]] = {}
        
        for error in errors:
            # Get field path
            field_path = ".".join(str(loc) for loc in error["loc"] if loc != "body")
            if not field_path:
                field_path = "general"
            
            # Get error message
            msg = error["msg"]
            
            # Add to formatted errors
            if field_path not in formatted_errors:
                formatted_errors[field_path] = []
            formatted_errors[field_path].append(msg)
        
        return formatted_errors


def setup_exception_handlers(
    app: FastAPI,
    include_stack_trace: bool = False,
    log_errors: bool = True,
    include_request_details: bool = False,
    custom_handlers: dict[type[Exception], Callable] = None
) -> GlobalExceptionHandler:
    """
    Setup global exception handlers for FastAPI application.
    
    Convenience function to quickly setup exception handling.
    
    Args:
        app: FastAPI application instance
        include_stack_trace: Include stack traces in responses (for development)
        log_errors: Log exceptions
        include_request_details: Include request details in error response
        custom_handlers: Dictionary of exception types to custom handler functions
    
    Returns:
        GlobalExceptionHandler instance
    
    Example:
        ```python
        from fastapi import FastAPI
        from building_blocks.api.exceptions import setup_exception_handlers
        
        app = FastAPI()
        
        # Development
        setup_exception_handlers(app, include_stack_trace=True)
        
        # Production
        setup_exception_handlers(app, include_stack_trace=False)
        ```
    """
    return GlobalExceptionHandler(
        app=app,
        include_stack_trace=include_stack_trace,
        log_errors=log_errors,
        include_request_details=include_request_details,
        custom_handlers=custom_handlers
    )
