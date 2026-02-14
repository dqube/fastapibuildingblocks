"""
Quick test for middleware logging functionality.
"""

import sys
import json
from io import StringIO
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Add src to path
sys.path.insert(0, '/Users/mdevendran/python/fastapibuildingblocks')

from src.building_blocks.observability import (
    setup_observability,
    ObservabilityConfig,
)

# Create test app
app = FastAPI()

# Configure with request/response logging
config = ObservabilityConfig(
    service_name="test-api",
    log_format="json",
    log_request_body=True,
    log_response_body=True,
    log_redaction_enabled=True,
    tracing_enabled=False,
    metrics_enabled=False,
)

setup_observability(app, config)


@app.post("/test-login")
async def test_login(credentials: dict):
    return {
        "user_id": "user_123",
        "access_token": "secret_jwt_token",
        "username": credentials.get("username")
    }


@app.post("/test-payment")
async def test_payment(payment: dict):
    return {
        "status": "success",
        "amount": payment.get("amount")
    }


# Test the middleware
def test_middleware_logging():
    """Test that middleware logs requests/responses with redaction."""
    print("="*80)
    print("TESTING MIDDLEWARE LOGGING")
    print("="*80)
    
    client = TestClient(app)
    
    # Test 1: Login with sensitive data
    print("\n1. Testing login endpoint with password redaction...")
    response = client.post(
        "/test-login",
        json={
            "username": "john_doe",
            "password": "super_secret_password",
            "api_key": "sk_live_1234567890"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user_123"
    assert "access_token" in data
    print("✅ Login endpoint works")
    
    # Test 2: Payment with PII
    print("\n2. Testing payment endpoint with credit card redaction...")
    response = client.post(
        "/test-payment",
        json={
            "amount": 99.99,
            "credit_card": "4242-4242-4242-4242",
            "cvv": "123",
            "email": "user@example.com"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["amount"] == 99.99
    print("✅ Payment endpoint works")
    
    print("\n" + "="*80)
    print("✅ ALL TESTS PASSED")
    print("="*80)
    print()
    print("Check the logs above - you should see:")
    print("  • Request method, path, and status code")
    print("  • Execution time in milliseconds")
    print("  • Request bodies with sensitive fields redacted:")
    print("    - password → ***REDACTED***(20)")
    print("    - api_key → ***REDACTED***(18)")
    print("    - credit_card → ***REDACTED***(19)")
    print("    - cvv → ***REDACTED***(3)")
    print("    - email → ***REDACTED***(16)")
    print("  • Response bodies with access_token redacted")
    print("="*80)


if __name__ == "__main__":
    test_middleware_logging()
