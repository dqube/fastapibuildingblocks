"""
Demo: Global Exception Handler with ProblemDetails

This example demonstrates how to use the GlobalExceptionHandler
similar to .NET's GlobalExceptionHandler with ProblemDetails (RFC 7807).
"""

import asyncio
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, EmailStr, field_validator

from building_blocks.api.exceptions import (
    setup_exception_handlers,
    GlobalExceptionHandler,
    ProblemDetails,
    ValidationProblemDetails,
    NotFoundException,
    BadRequestException,
    UnauthorizedException,
)


# ============================================================================
# Models
# ============================================================================

class CreateUserRequest(BaseModel):
    """Request model with validation."""
    email: EmailStr
    name: str = Field(min_length=2, max_length=100)
    age: int = Field(gt=0, le=150)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if v.lower() == "admin":
            raise ValueError("'admin' is a reserved name")
        return v


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    name: str
    age: int


# ============================================================================
# Example 1: Basic Setup (Development)
# ============================================================================

def create_dev_app() -> FastAPI:
    """Create FastAPI app with exception handler for development."""
    app = FastAPI(
        title="Development API",
        description="API with detailed error responses for debugging"
    )
    
    # Setup with stack traces and request details (for development)
    setup_exception_handlers(
        app,
        include_stack_trace=True,      # ⚠️ Include stack traces (DO NOT use in production!)
        log_errors=True,
        include_request_details=True   # Include request details in error response
    )
    
    return app


# ============================================================================
# Example 2: Production Setup
# ============================================================================

def create_prod_app() -> FastAPI:
    """Create FastAPI app with exception handler for production."""
    app = FastAPI(
        title="Production API",
        description="API with secure error responses"
    )
    
    # Setup for production (minimal error details)
    setup_exception_handlers(
        app,
        include_stack_trace=False,  # ✅ No stack traces in production
        log_errors=True,            # ✅ Log errors for monitoring
        include_request_details=False  # ✅ No sensitive request details
    )
    
    return app


# ============================================================================
# Example 3: Custom Exception Handlers
# ============================================================================

class CustomBusinessException(Exception):
    """Custom business logic exception."""
    
    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


async def handle_custom_business_exception(
    request: Request,
    exc: CustomBusinessException
) -> dict:
    """Custom handler for business exceptions."""
    from fastapi.responses import JSONResponse
    from building_blocks.api.exceptions import create_problem_details
    
    problem = create_problem_details(
        status=422,
        title="Business Rule Violation",
        detail=exc.message,
        instance=str(request.url.path),
        error_code=exc.error_code,
        business_context="payment_processing"
    )
    
    return JSONResponse(
        status_code=problem.status,
        content=problem.model_dump(exclude_none=True),
        headers={"Content-Type": "application/problem+json"}
    )


def create_app_with_custom_handlers() -> FastAPI:
    """Create FastAPI app with custom exception handlers."""
    app = FastAPI(title="API with Custom Handlers")
    
    # Register custom handlers
    GlobalExceptionHandler(
        app=app,
        include_stack_trace=False,
        log_errors=True,
        custom_handlers={
            CustomBusinessException: handle_custom_business_exception
        }
    )
    
    return app


# ============================================================================
# Sample Endpoints (for testing)
# ============================================================================

app = create_dev_app()  # or create_prod_app() for production


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Global Exception Handler Demo"}


@app.get("/users/{user_id}")
async def get_user(user_id: str):
    """
    Get user by ID - demonstrates NotFoundException.
    
    ProblemDetails response:
    {
        "type": "https://tools.ietf.org/html/rfc7231#section-6.5.4",
        "title": "Not Found",
        "status": 404,
        "detail": "User with ID '123' not found",
        "instance": "/users/123",
        "trace_id": "a1b2c3d4-5678-9012-3456-789012345678"
    }
    """
    # Simulate user not found
    if user_id not in ["1", "2", "3"]:
        raise NotFoundException(
            message=f"User with ID '{user_id}' not found",
            error_code="USER_NOT_FOUND"
        )
    
    return UserResponse(
        id=user_id,
        email=f"user{user_id}@example.com",
        name=f"User {user_id}",
        age=30
    )


@app.post("/users")
async def create_user(request: CreateUserRequest):
    """
    Create user - demonstrates validation error handling.
    
    ValidationProblemDetails response (if validation fails):
    {
        "type": "https://tools.ietf.org/html/rfc7231#section-6.5.1",
        "title": "One or more validation errors occurred",
        "status": 400,
        "detail": "Validation failed for the request",
        "instance": "/users",
        "trace_id": "a1b2c3d4-5678-9012-3456-789012345678",
        "errors": {
            "email": ["value is not a valid email address"],
            "age": ["Input should be greater than 0"]
        }
    }
    """
    # Simulate duplicate email
    if request.email == "taken@example.com":
        raise BadRequestException(
            message="A user with this email already exists",
            error_code="DUPLICATE_EMAIL"
        )
    
    return UserResponse(
        id=str(uuid4()),
        email=request.email,
        name=request.name,
        age=request.age
    )


@app.get("/protected")
async def protected_endpoint():
    """
    Protected endpoint - demonstrates UnauthorizedException.
    
    ProblemDetails response:
    {
        "type": "https://tools.ietf.org/html/rfc7235#section-3.1",
        "title": "Unauthorized",
        "status": 401,
        "detail": "Invalid or missing authentication token",
        "instance": "/protected",
        "trace_id": "a1b2c3d4-5678-9012-3456-789012345678"
    }
    """
    raise UnauthorizedException(
        message="Invalid or missing authentication token",
        error_code="AUTH_TOKEN_INVALID"
    )


@app.get("/error")
async def trigger_error():
    """
    Trigger unhandled exception - demonstrates generic error handling.
    
    ProblemDetails response:
    {
        "type": "https://tools.ietf.org/html/rfc7231#section-6.6.1",
        "title": "Internal Server Error",
        "status": 500,
        "detail": "An unexpected error occurred while processing your request",
        "instance": "/error",
        "trace_id": "a1b2c3d4-5678-9012-3456-789012345678",
        "stack_trace": "..." // Only in development mode
    }
    """
    # Simulate unexpected error
    raise ValueError("Something went wrong in business logic!")


@app.get("/division/{numerator}/{denominator}")
async def divide(numerator: int, denominator: int):
    """
    Division endpoint - demonstrates unhandled exception.
    
    Try: /division/10/0
    """
    result = numerator / denominator  # Will raise ZeroDivisionError
    return {"result": result}


@app.post("/business-operation")
async def business_operation():
    """
    Business operation - demonstrates custom exception handler.
    
    (Only works with create_app_with_custom_handlers)
    """
    raise CustomBusinessException(
        message="Insufficient funds for this transaction",
        error_code="INSUFFICIENT_FUNDS"
    )


# ============================================================================
# Testing Examples
# ============================================================================

async def test_exception_handling():
    """Test exception handling examples."""
    from httpx import AsyncClient
    
    print("="*80)
    print("GLOBAL EXCEPTION HANDLER DEMO")
    print("="*80)
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        
        # Test 1: Not Found
        print("\n1. Testing NotFoundException...")
        response = await client.get("/users/999")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Test 2: Validation Error
        print("\n2. Testing Validation Error...")
        response = await client.post(
            "/users",
            json={"email": "invalid-email", "name": "A", "age": -5}
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Test 3: Success Case
        print("\n3. Testing Success Case...")
        response = await client.post(
            "/users",
            json={"email": "test@example.com", "name": "Test User", "age": 25}
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Test 4: Unauthorized
        print("\n4. Testing UnauthorizedException...")
        response = await client.get("/protected")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Test 5: Generic Error
        print("\n5. Testing Generic Error (with stack trace in dev mode)...")
        response = await client.get("/error")
        print(f"   Status: {response.status_code}")
        result = response.json()
        # Don't print stack trace (too long)
        if "stack_trace" in result:
            result["stack_trace"] = "...(truncated)..."
        print(f"   Response: {result}")
    
    print("\n" + "="*80)
    print("✅ All tests completed!")
    print("="*80)


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*80)
    print("STARTING DEMO SERVER")
    print("="*80)
    print("\nEndpoints to test:")
    print("  GET  /                                  - Root")
    print("  GET  /users/1                           - Success: Get user")
    print("  GET  /users/999                         - Error: Not found")
    print("  POST /users                             - Create user (with validation)")
    print("       Body: {\"email\": \"test@example.com\", \"name\": \"Test\", \"age\": 25}")
    print("  POST /users                             - Error: Invalid data")
    print("       Body: {\"email\": \"invalid\", \"name\": \"A\", \"age\": -5}")
    print("  GET  /protected                         - Error: Unauthorized")
    print("  GET  /error                             - Error: Unhandled exception")
    print("  GET  /division/10/0                     - Error: Division by zero")
    print("  GET  /docs                              - API Documentation")
    print("\n" + "="*80)
    
    # Run test in background
    # asyncio.create_task(test_exception_handling())
    
    # Start server
    uvicorn.run(app, host="0.0.0.0", port=8001)
