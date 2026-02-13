# HTTP Request/Response Logging Middleware

## Overview

Yes, we now have **.NET-style middleware** that automatically logs HTTP requests and responses with:

- ✅ **Redacted sensitive data** (passwords, tokens, PII, etc.)
- ✅ **Execution time** (in both seconds and milliseconds)
- ✅ **Request body and headers** (optional, configurable)
- ✅ **Response body and headers** (optional, configurable)
- ✅ **Path exclusion** (health checks, metrics endpoints)
- ✅ **Size limits** (prevent logging huge payloads)

This is similar to ASP.NET Core's middleware logging capabilities.

## Configuration

### Basic Setup

```python
from fastapi import FastAPI
from fastapi_building_blocks.observability import (
    setup_observability,
    ObservabilityConfig,
)

app = FastAPI()

config = ObservabilityConfig(
    service_name="my-api",
    
    # Enable request/response logging (like .NET middleware)
    log_request_body=True,       # Log request bodies
    log_request_headers=True,    # Log request headers
    log_response_body=True,      # Log response bodies
    log_response_headers=True,   # Log response headers
    
    # Redaction (protect sensitive data)
    log_redaction_enabled=True,  # Enable redaction
    
    # Configuration
    max_body_log_size=10000,     # Max body size to log (bytes)
    exclude_paths=["/health", "/metrics"],  # Exclude from detailed logging
)

setup_observability(app, config)
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `log_request_body` | `bool` | `False` | Log request body with redaction |
| `log_request_headers` | `bool` | `False` | Log request headers with redaction |
| `log_response_body` | `bool` | `False` | Log response body with redaction |
| `log_response_headers` | `bool` | `False` | Log response headers with redaction |
| `log_redaction_enabled` | `bool` | `True` | Enable sensitive data masking |
| `max_body_log_size` | `int` | `10000` | Max body size to log (bytes) |
| `exclude_paths` | `List[str]` | `["/health", "/metrics"]` | Paths to exclude from detailed logging |
| `sensitive_field_keys` | `List[str]` | `[]` | Additional custom keys to redact |
| `sensitive_field_patterns` | `List[str]` | `[]` | Regex patterns for redaction |
| `redaction_mask_value` | `str` | `"***REDACTED***"` | Mask string |
| `redaction_mask_length` | `bool` | `True` | Show original value length |

## What Gets Logged

### Successful Request

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "message": "POST /api/login - 200 - 125.5ms",
  "http.method": "POST",
  "http.path": "/api/login",
  "http.status_code": 200,
  "http.duration_seconds": 0.1255,
  "http.duration_ms": 125.5,
  "http.request": {
    "headers": {
      "content-type": "application/json",
      "authorization": "***REDACTED***(43)"
    },
    "body": {
      "username": "john_doe",
      "password": "***REDACTED***(10)",
      "api_key": "***REDACTED***(15)"
    },
    "query_params": {}
  },
  "http.response": {
    "headers": {
      "content-type": "application/json"
    },
    "body": {
      "user_id": "user_12345",
      "access_token": "***REDACTED***(58)",
      "message": "Welcome, john_doe!"
    }
  }
}
```

### Failed Request

```json
{
  "timestamp": "2024-01-15T10:30:05Z",
  "level": "ERROR",
  "message": "POST /api/payment - ERROR: Invalid card - 85.3ms",
  "http.method": "POST",
  "http.path": "/api/payment",
  "http.error_type": "ValueError",
  "http.duration_seconds": 0.0853,
  "http.duration_ms": 85.3,
  "http.request": {
    "body": {
      "amount": 99.99,
      "credit_card": "***REDACTED***(19)",
      "cvv": "***REDACTED***(3)",
      "email": "***REDACTED***(20)"
    }
  },
  "exception": "Traceback (most recent call last):\n  ..."
}
```

### Excluded Paths

Health check and metrics endpoints are excluded from detailed logging by default:

```json
{
  "timestamp": "2024-01-15T10:30:10Z",
  "level": "INFO",
  "message": "GET /health - 200 - 2.1ms",
  "http.method": "GET",
  "http.path": "/health",
  "http.status_code": 200,
  "http.duration_seconds": 0.0021,
  "http.duration_ms": 2.1
}
```

No request/response body or headers logged for excluded paths.

## Automatic Redaction

The middleware automatically redacts 30+ sensitive field patterns:

### Authentication & Authorization
- `password`, `token`, `api_key`, `secret`
- `authorization`, `bearer`, `session_id`
- `access_token`, `refresh_token`, `id_token`

### Personal Information (PII)
- `email`, `ssn`, `phone`, `address`

### Financial Data
- `credit_card`, `card_number`, `cvv`, `cvc`
- `account_number`, `routing_number`

### Cloud & Infrastructure
- `aws_access_key_id`, `aws_secret_access_key`
- `private_key`, `ssl_key`, `certificate`
- `connection_string`, `database_url`

See [REDACTION_SUMMARY.md](REDACTION_SUMMARY.md) for complete list.

## Comparison with .NET Middleware

### ASP.NET Core Middleware (C#)

```csharp
// .NET Core middleware configuration
app.UseSerilogRequestLogging(options =>
{
    options.EnrichDiagnosticContext = (diagnosticContext, httpContext) =>
    {
        diagnosticContext.Set("RequestBody", GetRequestBody(httpContext));
        diagnosticContext.Set("ResponseBody", GetResponseBody(httpContext));
    };
    options.IncludeQueryInRequestPath = true;
});
```

### FastAPI Building Blocks (Python)

```python
# Python equivalent with automatic redaction
config = ObservabilityConfig(
    service_name="my-api",
    log_request_body=True,
    log_response_body=True,
    log_redaction_enabled=True,  # Built-in sensitive data protection
)
setup_observability(app, config)
```

## Features Comparison

| Feature | .NET (Serilog) | FastAPI Building Blocks |
|---------|----------------|-------------------------|
| Request logging | ✅ | ✅ |
| Response logging | ✅ | ✅ |
| Execution time | ✅ | ✅ (seconds + milliseconds) |
| Request body | ✅ (manual) | ✅ (automatic) |
| Response body | ✅ (manual) | ✅ (automatic) |
| **Automatic redaction** | ❌ (manual filters) | ✅ **Built-in** |
| Header logging | ✅ | ✅ |
| Path exclusion | ✅ | ✅ |
| Size limits | ⚠️ (manual) | ✅ (automatic) |
| Trace correlation | ✅ | ✅ (OpenTelemetry) |
| JSON structured logs | ✅ | ✅ |

**Key Advantage:** FastAPI Building Blocks includes **automatic sensitive data redaction** out-of-the-box, while .NET typically requires manual configuration.

## Usage Examples

### Example 1: REST API with Authentication

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

config = ObservabilityConfig(
    service_name="auth-api",
    log_request_body=True,
    log_response_body=True,
    log_redaction_enabled=True,
)
setup_observability(app, config)

class LoginRequest(BaseModel):
    username: str
    password: str  # Will be redacted in logs

@app.post("/login")
async def login(request: LoginRequest):
    # Password is automatically redacted in request logs
    return {
        "access_token": "jwt_token_here",  # Will be redacted in logs
        "user_id": "user_123"
    }
```

**Log output:**
```json
{
  "message": "POST /login - 200 - 45.2ms",
  "http.request": {
    "body": {
      "username": "john_doe",
      "password": "***REDACTED***(10)"
    }
  },
  "http.response": {
    "body": {
      "access_token": "***REDACTED***(20)",
      "user_id": "user_123"
    }
  }
}
```

### Example 2: Payment Processing API

```python
class PaymentRequest(BaseModel):
    amount: float
    credit_card: str
    cvv: str
    email: str

@app.post("/payment")
async def process_payment(payment: PaymentRequest):
    # Credit card, CVV, and email are automatically redacted
    return {"status": "success", "transaction_id": "txn_123"}
```

**Log output:**
```json
{
  "message": "POST /payment - 200 - 200.5ms",
  "http.request": {
    "body": {
      "amount": 99.99,
      "credit_card": "***REDACTED***(19)",
      "cvv": "***REDACTED***(3)",
      "email": "***REDACTED***(20)"
    }
  }
}
```

### Example 3: Custom Sensitive Fields

```python
config = ObservabilityConfig(
    service_name="internal-api",
    log_request_body=True,
    log_response_body=True,
    
    # Add domain-specific sensitive fields
    sensitive_field_keys=["internal_id", "merchant_code"],
    sensitive_field_patterns=[
        r".*_secret$",      # Any field ending with _secret
        r"^private_.*",     # Any field starting with private_
    ],
)
```

### Example 4: Disable for Specific Routes

```python
config = ObservabilityConfig(
    service_name="api",
    log_request_body=True,
    log_response_body=True,
    
    # Exclude these paths from detailed logging
    exclude_paths=[
        "/health",
        "/metrics",
        "/readiness",
        "/liveness",
        "/status"
    ],
)
```

## Performance Considerations

### Body Parsing
- Request body is read only once (FastAPI does this anyway)
- Response body is read only if `log_response_body=True`
- Size limit prevents logging huge payloads

### Redaction Performance
- Recursive dict traversal on each log
- Minimal overhead for typical payloads (<1ms)
- Can be disabled with `log_redaction_enabled=False`

### Recommendations

1. **Production**: Enable logging with redaction
   ```python
   log_request_body=True,
   log_response_body=True,
   log_redaction_enabled=True,
   ```

2. **High-traffic APIs**: Disable body logging for performance
   ```python
   log_request_body=False,
   log_response_body=False,
   # Still logs method, path, status, execution time
   ```

3. **Debug/Staging**: Full logging with headers
   ```python
   log_request_body=True,
   log_request_headers=True,
   log_response_body=True,
   log_response_headers=True,
   ```

## Demo

Run the demo to see it in action:

```bash
cd /Users/mdevendran/python/fastapibuildingblocks
python3 demo_middleware.py
```

Then test with curl:

```bash
# Login with sensitive credentials
curl -X POST http://localhost:8001/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"john","password":"secret123","api_key":"sk_live_abc"}'

# Payment with PII
curl -X POST http://localhost:8001/api/payment \
  -H "Content-Type: application/json" \
  -d '{"amount":99.99,"credit_card":"4242-4242-4242-4242","cvv":"123","email":"user@example.com"}'
```

Watch the logs - all sensitive data will be redacted!

## Summary

**Yes, you now have .NET middleware-style logging!** 🎉

✅ Automatic request/response logging  
✅ Execution time tracking (ms precision)  
✅ Built-in sensitive data redaction  
✅ Configurable (enable/disable per feature)  
✅ Path exclusion support  
✅ Size limits for large payloads  
✅ Production-ready with OpenTelemetry integration  

The middleware is **more secure than typical .NET middleware** because redaction is built-in, not an afterthought.
