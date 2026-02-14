# Global Exception Handler with ProblemDetails

This implementation provides .NET-style global exception handling with RFC 7807 ProblemDetails support for FastAPI applications.

## 🎯 Features

### ✅ RFC 7807 Compliance
- Standard `ProblemDetails` response format
- Consistent error structure across all endpoints
- Machine-readable error types with URIs
- Human-readable titles and details

### ✅ Validation Error Handling
- `ValidationProblemDetails` for validation errors
- Field-level error messages
- Automatic conversion of Pydantic validation errors
- FastAPI request validation support

### ✅ Distributed Tracing
- Automatic trace ID extraction from headers (`X-Trace-Id`, `traceparent`)
- Trace ID included in all error responses
- Correlation with OpenTelemetry spans
- Request state integration

### ✅ Comprehensive Exception Coverage
- Custom API exceptions (`NotFoundException`, `BadRequestException`, etc.)
- FastAPI/Starlette HTTP exceptions
- Pydantic validation errors
- Generic unhandled exceptions
- Custom exception handlers

### ✅ Production-Ready
- Configurable stack trace inclusion (dev vs prod)
- Automatic error logging
- Sensitive data protection
- Customizable error details level

---

## 📦 Components

### 1. ProblemDetails Model

RFC 7807 compliant error response model.

```python
from building_blocks.api.exceptions import ProblemDetails, create_problem_details

# Create a ProblemDetails response
problem = create_problem_details(
    status=404,
    title="Not Found",
    detail="User with ID '123' not found",
    instance="/users/123",
    trace_id="a1b2c3d4-5678-9012-3456-789012345678",
    error_code="USER_NOT_FOUND",
    resource_type="User",
    resource_id="123"
)
```

**Response:**
```json
{
  "type": "https://tools.ietf.org/html/rfc7231#section-6.5.4",
  "title": "Not Found",
  "status": 404,
  "detail": "User with ID '123' not found",
  "instance": "/users/123",
  "trace_id": "a1b2c3d4-5678-9012-3456-789012345678",
  "error_code": "USER_NOT_FOUND",
  "resource_type": "User",
  "resource_id": "123"
}
```

### 2. ValidationProblemDetails

Extended ProblemDetails for validation errors (similar to .NET's `ValidationProblemDetails`).

```python
from building_blocks.api.exceptions import ValidationProblemDetails

problem = ValidationProblemDetails(
    status=400,
    title="Validation Error",
    detail="One or more validation errors occurred",
    instance="/users",
    errors={
        "email": ["value is not a valid email address"],
        "age": ["Input should be greater than 0"]
    }
)
```

**Response:**
```json
{
  "type": "https://tools.ietf.org/html/rfc7231#section-6.5.1",
  "title": "Validation Error",
  "status": 400,
  "detail": "One or more validation errors occurred",
  "instance": "/users",
  "errors": {
    "email": ["value is not a valid email address"],
    "age": ["Input should be greater than 0"]
  }
}
```

### 3. GlobalExceptionHandler

Centralized exception handler (similar to .NET's `GlobalExceptionHandler`).

```python
from building_blocks.api.exceptions import GlobalExceptionHandler

# Manual setup
handler = GlobalExceptionHandler(
    app=app,
    include_stack_trace=False,  # Production: hide stack traces
    log_errors=True,            # Enable error logging
    include_request_details=False  # Production: hide request details
)

# Or use convenience function
from building_blocks.api.exceptions import setup_exception_handlers

setup_exception_handlers(
    app=app,
    include_stack_trace=False,
    log_errors=True
)
```

---

## 🚀 Quick Start

### Basic Setup (Development)

```python
from fastapi import FastAPI
from building_blocks.api.exceptions import setup_exception_handlers

app = FastAPI()

# Setup with detailed error responses for development
setup_exception_handlers(
    app,
    include_stack_trace=True,      # ⚠️ Show stack traces
    log_errors=True,
    include_request_details=True   # Show request details
)
```

### Production Setup

```python
from fastapi import FastAPI
from building_blocks.api.exceptions import setup_exception_handlers

app = FastAPI()

# Setup with minimal error details for production
setup_exception_handlers(
    app,
    include_stack_trace=False,  # ✅ Hide stack traces
    log_errors=True,            # ✅ Log errors
    include_request_details=False  # ✅ Hide request details
)
```

### Using Custom Exceptions

```python
from building_blocks.api.exceptions import NotFoundException, BadRequestException

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    user = await user_repository.get(user_id)
    if not user:
        raise NotFoundException(
            message=f"User with ID '{user_id}' not found",
            error_code="USER_NOT_FOUND",
            resource_type="User",
            resource_id=user_id
        )
    return user

@app.post("/users")
async def create_user(request: CreateUserRequest):
    if await user_repository.exists(request.email):
        raise BadRequestException(
            message="A user with this email already exists",
            error_code="DUPLICATE_EMAIL"
        )
    return await user_repository.create(request)
```

### Custom Exception Handlers

```python
from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from building_blocks.api.exceptions import GlobalExceptionHandler, create_problem_details

class PaymentException(Exception):
    def __init__(self, message: str, amount: float):
        self.message = message
        self.amount = amount

async def handle_payment_exception(request: Request, exc: PaymentException):
    problem = create_problem_details(
        status=422,
        title="Payment Processing Error",
        detail=exc.message,
        instance=str(request.url.path),
        amount=exc.amount,
        currency="USD"
    )
    return JSONResponse(
        status_code=problem.status,
        content=problem.model_dump(exclude_none=True),
        headers={"Content-Type": "application/problem+json"}
    )

app = FastAPI()
GlobalExceptionHandler(
    app=app,
    custom_handlers={
        PaymentException: handle_payment_exception
    }
)
```

---

## 📋 Exception Types

The framework automatically handles these exception types:

### 1. APIException (Custom)
- `NotFoundException` (404)
- `BadRequestException` (400)
- `UnauthorizedException` (401)
- `ForbiddenException` (403)
- `ConflictException` (409)

### 2. FastAPI HTTP Exceptions
- All `HTTPException` from FastAPI/Starlette
- Automatic conversion to ProblemDetails

### 3. Validation Errors
- FastAPI request validation (`RequestValidationError`)
- Pydantic model validation (`ValidationError`)
- Field-level error details

### 4. Generic Exceptions
- Unhandled exceptions (500)
- Stack trace in development mode
- Generic error message in production

---

## 🔍 Trace ID Support

The handler automatically extracts trace IDs from:

1. **HTTP Headers:**
   - `X-Trace-Id`: Custom trace ID
   - `traceparent`: W3C Trace Context (OpenTelemetry)
   - `X-Request-Id`: Alternative request ID

2. **Request State:**
   - `request.state.trace_id`
   - `request.state.span_id`

3. **OpenTelemetry Context:**
   - Automatic span context extraction

**Example:**
```python
from opentelemetry import trace

@app.get("/users/{user_id}")
async def get_user(request: Request, user_id: str):
    # Trace ID automatically included in error response
    span = trace.get_current_span()
    span.set_attribute("user_id", user_id)
    
    if not user:
        raise NotFoundException(...)
    # Error response will include trace_id from span context
```

---

## 📊 Error Response Examples

### Not Found (404)
```json
{
  "type": "https://tools.ietf.org/html/rfc7231#section-6.5.4",
  "title": "Not Found",
  "status": 404,
  "detail": "User with ID '999' not found",
  "instance": "/users/999",
  "trace_id": "12345678-1234-1234-1234-123456789012",
  "error_code": "USER_NOT_FOUND",
  "resource_type": "User",
  "resource_id": "999"
}
```

### Validation Error (400)
```json
{
  "type": "https://tools.ietf.org/html/rfc7231#section-6.5.1",
  "title": "One or more validation errors occurred",
  "status": 400,
  "detail": "Validation failed for the request",
  "instance": "/users",
  "trace_id": "12345678-1234-1234-1234-123456789012",
  "errors": {
    "email": ["value is not a valid email address"],
    "name": ["String should have at least 2 characters"],
    "age": ["Input should be greater than 0"]
  }
}
```

### Unauthorized (401)
```json
{
  "type": "https://tools.ietf.org/html/rfc7235#section-3.1",
  "title": "Unauthorized",
  "status": 401,
  "detail": "Invalid or missing authentication token",
  "instance": "/protected",
  "trace_id": "12345678-1234-1234-1234-123456789012",
  "error_code": "AUTH_TOKEN_INVALID"
}
```

### Internal Server Error (500) - Development
```json
{
  "type": "https://tools.ietf.org/html/rfc7231#section-6.6.1",
  "title": "Internal Server Error",
  "status": 500,
  "detail": "An unexpected error occurred",
  "instance": "/api/operation",
  "trace_id": "12345678-1234-1234-1234-123456789012",
  "stack_trace": "Traceback (most recent call last):\n  File ...",
  "exception_type": "ValueError"
}
```

### Internal Server Error (500) - Production
```json
{
  "type": "https://tools.ietf.org/html/rfc7231#section-6.6.1",
  "title": "Internal Server Error",
  "status": 500,
  "detail": "An unexpected error occurred while processing your request",
  "instance": "/api/operation",
  "trace_id": "12345678-1234-1234-1234-123456789012"
}
```

---

## 🧪 Testing

Run the demo application:

```bash
# Start the demo server
python demo_exception_handler.py

# Test endpoints
curl http://localhost:8001/users/999              # 404 Not Found
curl http://localhost:8001/protected              # 401 Unauthorized
curl -X POST http://localhost:8001/users \
  -H "Content-Type: application/json" \
  -d '{"email":"invalid","name":"A","age":-5}'   # 400 Validation Error
curl http://localhost:8001/error                  # 500 Internal Server Error
curl http://localhost:8001/division/10/0          # 500 Division by Zero

# View OpenAPI docs
open http://localhost:8001/docs
```

---

## 🔧 Configuration Options

```python
GlobalExceptionHandler(
    app=app,
    
    # Stack trace configuration
    include_stack_trace=False,      # Show full stack trace in responses
    
    # Logging configuration
    log_errors=True,                # Log all exceptions
    
    # Request details
    include_request_details=False,  # Include request info in 500 errors
    
    # Custom handlers
    custom_handlers={
        CustomException: custom_handler_function
    }
)
```

**Recommendation:**
- **Development:** `include_stack_trace=True`, `include_request_details=True`
- **Production:** `include_stack_trace=False`, `include_request_details=False`

---

## 🎭 Comparison with .NET

| Feature | .NET Core | FastAPI Building Blocks |
|---------|-----------|-------------------------|
| ProblemDetails | ✅ Built-in | ✅ Implemented |
| ValidationProblemDetails | ✅ Built-in | ✅ Implemented |
| Global Exception Handler | ✅ `UseExceptionHandler()` | ✅ `setup_exception_handlers()` |
| RFC 7807 Compliance | ✅ Full | ✅ Full |
| Trace ID Support | ✅ Activity.Current | ✅ OpenTelemetry |
| Custom Exception Mapping | ✅ Status code middleware | ✅ Custom handlers |
| Development/Production Modes | ✅ Environment-based | ✅ Configuration-based |

---

## 📚 References

- [RFC 7807 - Problem Details for HTTP APIs](https://tools.ietf.org/html/rfc7807)
- [.NET ProblemDetails](https://learn.microsoft.com/en-us/dotnet/api/microsoft.aspnetcore.mvc.problemdetails)
- [FastAPI Exception Handling](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [OpenTelemetry Tracing](https://opentelemetry.io/docs/instrumentation/python/)

---

## ✅ Next Steps

1. **Integrate with existing FastAPI apps:**
   ```python
   setup_exception_handlers(app, include_stack_trace=False, log_errors=True)
   ```

2. **Add trace ID middleware** (if not already using OpenTelemetry):
   ```python
   from building_blocks.observability.middleware import TraceIdMiddleware
   app.add_middleware(TraceIdMiddleware)
   ```

3. **Use custom exceptions** in your domain/application layers:
   ```python
   from building_blocks.api.exceptions import NotFoundException
   raise NotFoundException(message="Resource not found", error_code="RESOURCE_NOT_FOUND")
   ```

4. **Monitor error rates** using the trace IDs in your logging/observability platform

5. **Create custom exception handlers** for domain-specific errors

---

## 💡 Tips

1. **Always include error_code** for machine-readable error identification
2. **Use trace_id** for correlating errors across distributed systems
3. **Hide stack traces in production** to avoid exposing internal details
4. **Log all errors** even if not showing details to users
5. **Use ValidationProblemDetails** for complex validation scenarios
6. **Create domain-specific exceptions** by extending `APIException`
7. **Test error responses** in development with `include_stack_trace=True`

---

**Implementation Complete!** 🎉

You now have a production-ready global exception handler with ProblemDetails support, matching .NET's capabilities.
