"""
Demo of .NET-style middleware logging with redacted request/response and execution time.
"""

from fastapi import FastAPI, Request
from pydantic import BaseModel
import uvicorn

from src.fastapi_building_blocks.observability import (
    setup_observability,
    ObservabilityConfig,
)


# Request/Response models
class LoginRequest(BaseModel):
    username: str
    password: str
    api_key: str


class LoginResponse(BaseModel):
    user_id: str
    access_token: str
    message: str


class PaymentRequest(BaseModel):
    amount: float
    credit_card: str
    cvv: str
    email: str


# Create FastAPI app
app = FastAPI(title="Request/Response Logging Demo")


# Configure observability with request/response logging
config = ObservabilityConfig(
    service_name="demo-api",
    environment="development",
    
    # Enable logging features (similar to .NET middleware)
    logging_enabled=True,
    log_format="json",
    log_level="INFO",
    
    # Enable request/response body and headers logging
    log_request_body=True,
    log_request_headers=True,
    log_response_body=True,
    log_response_headers=True,
    
    # Enable redaction to protect sensitive data
    log_redaction_enabled=True,
    redaction_mask_value="***REDACTED***",
    redaction_mask_length=True,
    
    # Configuration options
    max_body_log_size=10000,
    exclude_paths=["/health", "/metrics"],  # Don't log details for these paths
    
    # Disable other observability features for this demo
    tracing_enabled=False,
    metrics_enabled=False,
)

setup_observability(app, config)


@app.get("/health")
async def health():
    """Health check endpoint (excluded from detailed logging)."""
    return {"status": "healthy"}


@app.post("/api/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Login endpoint - demonstrates request/response body logging with redaction.
    
    The middleware will automatically log:
    - Request body with password and api_key redacted
    - Response body with access_token redacted
    - Execution time in milliseconds
    """
    # Simulate processing
    import time
    time.sleep(0.1)  # 100ms processing time
    
    return LoginResponse(
        user_id="user_12345",
        access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.signature",
        message=f"Welcome, {request.username}!"
    )


@app.post("/api/payment")
async def process_payment(payment: PaymentRequest):
    """
    Payment processing endpoint - demonstrates PII redaction.
    
    The middleware will automatically log:
    - Request body with credit_card, cvv, and email redacted
    - Response body
    - Execution time
    """
    # Simulate payment processing
    import time
    time.sleep(0.2)  # 200ms processing time
    
    return {
        "transaction_id": "txn_abc123",
        "status": "success",
        "amount": payment.amount,
        "email": payment.email,  # This will be redacted in logs
    }


@app.get("/api/users/{user_id}")
async def get_user(user_id: str, token: str = None):
    """
    Get user endpoint - demonstrates query parameter logging with redaction.
    
    The middleware will log:
    - Query parameters (token will be redacted)
    - Execution time
    """
    import time
    time.sleep(0.05)  # 50ms processing time
    
    return {
        "user_id": user_id,
        "username": "john_doe",
        "email": "john@example.com",  # Will be redacted in response logs
    }


@app.post("/api/error")
async def error_endpoint():
    """
    Error endpoint - demonstrates error logging with execution time.
    """
    # Simulate some processing before error
    import time
    time.sleep(0.03)  # 30ms before error
    
    raise ValueError("Simulated error for demonstration")


if __name__ == "__main__":
    print("="*80)
    print(".NET-STYLE MIDDLEWARE LOGGING DEMONSTRATION")
    print("="*80)
    print()
    print("The middleware will log:")
    print("  ✅ Request method, path, and status code")
    print("  ✅ Execution time in milliseconds")
    print("  ✅ Request body with sensitive data REDACTED")
    print("  ✅ Response body with sensitive data REDACTED")
    print("  ✅ Request/response headers (optional)")
    print()
    print("Try these endpoints:")
    print()
    print("1. Login (with sensitive credentials):")
    print('   curl -X POST http://localhost:8001/api/login \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"username":"john","password":"secret123","api_key":"sk_live_abc"}\'')
    print()
    print("2. Payment (with PII):")
    print('   curl -X POST http://localhost:8001/api/payment \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"amount":99.99,"credit_card":"4242-4242-4242-4242","cvv":"123","email":"user@example.com"}\'')
    print()
    print("3. Get user (with token in query):")
    print('   curl "http://localhost:8001/api/users/user123?token=secret_token_abc"')
    print()
    print("4. Error endpoint:")
    print('   curl -X POST http://localhost:8001/api/error')
    print()
    print("="*80)
    print("Watch the logs below - passwords, tokens, emails, etc. will be redacted!")
    print("="*80)
    print()
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
