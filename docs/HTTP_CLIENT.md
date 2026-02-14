# HTTP Client Wrapper

Production-ready HTTP client for external API communication with comprehensive resilience patterns and observability.

## 🎯 Features

- ✅ **Multiple Authentication Strategies** - Bearer, Basic, OAuth2, API Key, Custom Headers
- ✅ **Automatic Header Injection** - Correlation ID, Consumer ID
- ✅ **Retry Logic** - Exponential backoff with jitter
- ✅ **Circuit Breaker** - Prevent cascading failures
- ✅ **OpenTelemetry Tracing** - Distributed tracing integration
- ✅ **Request/Response Logging** - Configurable with sensitive data protection
- ✅ **Connection Pooling** - Efficient HTTP/1.1 and HTTP/2 support
- ✅ **Timeout Configuration** - Per-request and global timeouts
- ✅ **Async/Await** - Full async support with httpx

---

## 📦 Installation

The HTTP client is included in the core package:

```bash
pip install -e .
```

Dependencies:
- `httpx>=0.25.0` - Modern async HTTP client
- `opentelemetry-api>=1.20.0` - Tracing integration

---

## 🚀 Quick Start

### Basic Usage

```python
from building_blocks.infrastructure.http import HttpClient, HttpClientConfig

# Configure client
config = HttpClientConfig(
    base_url="https://api.example.com",
    consumer_id="my-service-v1",
    timeout=30.0,
)

# Use client
async with HttpClient(config) as client:
    response = await client.get("/users/123")
    print(response.json())
```

### With Authentication

```python
from building_blocks.infrastructure.http import (
    HttpClient,
    HttpClientConfig,
    BearerAuth,
)

config = HttpClientConfig(
    base_url="https://api.example.com",
    auth_strategy=BearerAuth(token="your_jwt_token"),
    consumer_id="my-service",
)

async with HttpClient(config) as client:
    response = await client.post(
        "/orders",
        json={"product_id": "123", "quantity": 2}
    )
```

---

## 🔐 Authentication Strategies

### 1. Bearer Token (JWT)

```python
from building_blocks.infrastructure.http import BearerAuth

config = HttpClientConfig(
    base_url="https://api.example.com",
    auth_strategy=BearerAuth(token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
)
```

Headers sent:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 2. Basic Authentication

```python
from building_blocks.infrastructure.http import BasicAuth

config = HttpClientConfig(
    base_url="https://api.example.com",
    auth_strategy=BasicAuth(username="user", password="pass")
)
```

Headers sent:
```
Authorization: Basic dXNlcjpwYXNz
```

### 3. API Key

```python
from building_blocks.infrastructure.http import ApiKeyAuth

# API Key in header
config = HttpClientConfig(
    base_url="https://api.example.com",
    auth_strategy=ApiKeyAuth(
        api_key="your_api_key",
        header_name="X-API-Key",
        location="header"
    )
)

# API Key in query parameter
config = HttpClientConfig(
    base_url="https://api.example.com",
    auth_strategy=ApiKeyAuth(
        api_key="your_api_key",
        location="query"  # Adds ?api_key=your_api_key
    )
)
```

### 4. OAuth2 Client Credentials

Automatically fetches and refreshes tokens:

```python
from building_blocks.infrastructure.http import OAuth2ClientCredentials

config = HttpClientConfig(
    base_url="https://api.example.com",
    auth_strategy=OAuth2ClientCredentials(
        token_url="https://auth.example.com/oauth/token",
        client_id="your_client_id",
        client_secret="your_client_secret",
        scope="read:api write:api"
    )
)

# Token is automatically fetched on first request
# Token is automatically refreshed when expired
async with HttpClient(config) as client:
    response = await client.get("/protected/resource")
```

### 5. Custom Headers

```python
from building_blocks.infrastructure.http import CustomHeaderAuth

config = HttpClientConfig(
    base_url="https://api.example.com",
    auth_strategy=CustomHeaderAuth(headers={
        "X-Auth-Token": "custom_token",
        "X-API-Secret": "secret_key",
    })
)
```

---

## 🔄 Retry Logic

### Exponential Backoff (Default)

```python
from building_blocks.infrastructure.http import ExponentialBackoff

retry_policy = ExponentialBackoff(
    max_retries=3,          # Maximum retry attempts
    base_delay=1.0,         # Initial delay (seconds)
    max_delay=60.0,         # Maximum delay (seconds)
    exponential_base=2.0,   # Exponential multiplier
    jitter=True,            # Add random jitter to prevent thundering herd
)

config = HttpClientConfig(
    base_url="https://api.example.com",
    retry_policy=retry_policy,
)
```

**Retry Delays:**
- Attempt 1: ~1s (base_delay * 2^0 with jitter)
- Attempt 2: ~2s (base_delay * 2^1 with jitter)
- Attempt 3: ~4s (base_delay * 2^2 with jitter)

**Retryable Status Codes:**
- 408 - Request Timeout
- 429 - Too Many Requests
- 500 - Internal Server Error
- 502 - Bad Gateway
- 503 - Service Unavailable
- 504 - Gateway Timeout

**Retryable Exceptions:**
- Connection errors
- Timeout errors
- Network errors

### Fixed Retry

```python
from building_blocks.infrastructure.http.retry import FixedRetry

retry_policy = FixedRetry(
    max_retries=3,
    delay=2.0,  # Fixed 2 second delay
)
```

### No Retry

```python
from building_blocks.infrastructure.http import NoRetry

config = HttpClientConfig(
    base_url="https://api.example.com",
    retry_policy=NoRetry(),  # Disable retries
)
```

---

## 🔌 Circuit Breaker

Prevents cascading failures by "opening" after repeated failures:

```python
config = HttpClientConfig(
    base_url="https://api.example.com",
    enable_circuit_breaker=True,
    circuit_breaker_failure_threshold=5,  # Open after 5 failures
    circuit_breaker_timeout=60.0,         # Wait 60s before half-open
)

async with HttpClient(config) as client:
    try:
        response = await client.get("/endpoint")
    except CircuitBreakerError:
        print("Circuit breaker is OPEN - service is unavailable")
    
    # Check circuit breaker stats
    stats = client.get_circuit_breaker_stats()
    print(f"State: {stats['state']}")  # closed, open, or half_open
    print(f"Failures: {stats['failure_count']}/{stats['failure_threshold']}")
```

**Circuit Breaker States:**

1. **CLOSED** (Normal)
   - Requests pass through normally
   - Failures are counted
   - Opens after threshold reached

2. **OPEN** (Service Down)
   - All requests immediately fail with `CircuitBreakerError`
   - No requests reach the downstream service
   - After timeout, transitions to HALF_OPEN

3. **HALF_OPEN** (Testing Recovery)
   - Allows a test request through
   - If successful → back to CLOSED
   - If fails → back to OPEN

---

## 🆔 Correlation ID & Consumer ID

### Automatic Correlation ID

Every request gets a unique correlation ID for distributed tracing:

```python
async with HttpClient(config) as client:
    # Correlation ID automatically generated
    response = await client.get("/users/123")
    # Header sent: X-Correlation-Id: a1b2c3d4-5678-9012-3456-789012345678
```

### Custom Correlation ID

Pass existing correlation ID to trace requests across services:

```python
correlation_id = "existing-trace-id-from-upstream"

async with HttpClient(config) as client:
    # Service A → Service B
    response1 = await client.get("/orders", correlation_id=correlation_id)
    
    # Service B → Service C (same trace)
    response2 = await client.post("/payments", 
                                   json={"order_id": "123"}, 
                                   correlation_id=correlation_id)
```

### Consumer ID

Identifies the calling service:

```python
config = HttpClientConfig(
    base_url="https://api.example.com",
    consumer_id="ecommerce-service-v2.1.0",  # Identifies your service
)

# Headers sent:
# X-Consumer-Id: ecommerce-service-v2.1.0
# X-Correlation-Id: a1b2c3d4-5678-9012-3456-789012345678
```

### Default Headers

Add default headers to all requests:

```python
config = HttpClientConfig(
    base_url="https://api.example.com",
    consumer_id="mobile-app",
    default_headers={
        "X-App-Version": "2.1.0",
        "X-Platform": "iOS",
        "Accept-Language": "en-US",
    }
)
```

---

## 📊 Logging & Observability

### Request/Response Logging

```python
config = HttpClientConfig(
    base_url="https://api.example.com",
    log_requests=True,           # Log outgoing requests
    log_responses=True,          # Log incoming responses
    log_request_body=False,      # ⚠️ Don't log sensitive request data
    log_response_body=False,     # ⚠️ Don't log large responses
)
```

**Log Output:**
```
INFO - HTTP Request: POST https://api.example.com/orders
INFO - HTTP Response: 201 for POST https://api.example.com/orders
```

### OpenTelemetry Tracing

Automatic distributed tracing integration:

```python
config = HttpClientConfig(
    base_url="https://api.example.com",
    enable_tracing=True,  # Enable OpenTelemetry traces
)

async with HttpClient(config) as client:
    response = await client.get("/users/123")
    # Creates span: "HTTP GET /users/123"
    # Attributes: http.method, http.url, http.status_code, correlation_id
```

**Trace Attributes:**
- `http.method` - HTTP method (GET, POST, etc.)
- `http.url` - Full request URL
- `http.status_code` - Response status code
- `correlation_id` - Correlation ID for request tracing

---

## 🔧 Configuration

### Complete Configuration Example

```python
from building_blocks.infrastructure.http import (
    HttpClientConfig,
    BearerAuth,
    ExponentialBackoff,
)

config = HttpClientConfig(
    # Base configuration
    base_url="https://api.example.com",
    timeout=30.0,                    # Request timeout in seconds
    
    # Authentication
    auth_strategy=BearerAuth(token="your_token"),
    
    # Retry configuration
    retry_policy=ExponentialBackoff(
        max_retries=3,
        base_delay=1.0,
        max_delay=60.0,
    ),
    
    # Circuit breaker
    enable_circuit_breaker=True,
    circuit_breaker_failure_threshold=5,
    circuit_breaker_timeout=60.0,
    
    # Headers
    consumer_id="my-service-v1",
    default_headers={
        "X-Custom-Header": "value",
    },
    
    # Logging
    log_requests=True,
    log_responses=True,
    log_request_body=False,      # Protect sensitive data
    log_response_body=False,     # Avoid large logs
    
    # Tracing
    enable_tracing=True,
    
    # HTTP/2
    http2=False,                 # Enable HTTP/2
    
    # Connection limits
    max_connections=100,
    max_keepalive_connections=20,
)
```

---

## 🎯 HTTP Methods

All standard HTTP methods are supported:

```python
async with HttpClient(config) as client:
    # GET
    response = await client.get("/users/123", params={"include": "profile"})
    
    # POST
    response = await client.post("/users", json={"name": "John", "email": "john@example.com"})
    
    # PUT
    response = await client.put("/users/123", json={"name": "Jane"})
    
    # PATCH
    response = await client.patch("/users/123", json={"email": "new@example.com"})
    
    # DELETE
    response = await client.delete("/users/123")
    
    # Generic request
    response = await client.request(
        "POST",
        "/custom-endpoint",
        headers={"X-Custom": "value"},
        json={"data": "value"}
    )
```

---

## 💼 Real-World Examples

### Example 1: Payment Gateway Integration

```python
from building_blocks.infrastructure.http import (
    HttpClient,
    HttpClientConfig,
    ApiKeyAuth,
    ExponentialBackoff,
)

# Configure payment gateway client
config = HttpClientConfig(
    base_url="https://api.stripe.com",
    auth_strategy=ApiKeyAuth(
        api_key="sk_live_...",
        header_name="Authorization",
        location="header"
    ),
    consumer_id="ecommerce-backend",
    retry_policy=ExponentialBackoff(max_retries=3, base_delay=2.0),
    enable_circuit_breaker=True,
    circuit_breaker_failure_threshold=5,
    timeout=30.0,
    default_headers={"X-API-Version": "2024-02-01"},
    log_request_body=False,  # Don't log payment data
)

async def process_payment(order_id: str, amount: int):
    async with HttpClient(config) as client:
        # Create payment intent
        response = await client.post(
            "/v1/payment_intents",
            json={
                "amount": amount,
                "currency": "usd",
                "metadata": {"order_id": order_id}
            }
        )
        return response.json()
```

### Example 2: Microservice Communication

```python
# Service A calling Service B
async def call_order_service(user_id: str, correlation_id: str):
    config = HttpClientConfig(
        base_url="http://order-service:8000",
        consumer_id="user-service-v1",
        timeout=10.0,
    )
    
    async with HttpClient(config) as client:
        response = await client.get(
            f"/users/{user_id}/orders",
            correlation_id=correlation_id  # Pass correlation for tracing
        )
        return response.json()
```

### Example 3: External API with OAuth2

```python
from building_blocks.infrastructure.http import OAuth2ClientCredentials

config = HttpClientConfig(
    base_url="https://api.example.com",
    auth_strategy=OAuth2ClientCredentials(
        token_url="https://auth.example.com/oauth/token",
        client_id="your_client_id",
        client_secret="your_client_secret",
        scope="read:data write:data"
    ),
    consumer_id="data-sync-service",
)

async def sync_data():
    async with HttpClient(config) as client:
        # Token automatically fetched/refreshed
        response = await client.get("/api/data")
        return response.json()
```

### Example 4: Concurrent Requests

```python
import asyncio

async def fetch_multiple_users(user_ids: list[str]):
    config = HttpClientConfig(
        base_url="https://api.example.com",
        consumer_id="batch-processor",
        max_connections=50,  # Allow many concurrent connections
    )
    
    async with HttpClient(config) as client:
        # Make concurrent requests
        tasks = [
            client.get(f"/users/{user_id}")
            for user_id in user_ids
        ]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]
```

---

## 🧪 Testing

Run the demo to see all features in action:

```bash
python demo_http_client.py
```

**Examples demonstrated:**
1. Bearer token authentication
2. Basic authentication
3. API key authentication
4. OAuth2 client credentials
5. Retry logic with exponential backoff
6. Circuit breaker pattern
7. Custom correlation ID
8. Custom headers + consumer ID
9. Multiple concurrent requests
10. Real-world payment API integration

---

## 📋 Best Practices

### ✅ Do's

1. **Use correlation IDs** for distributed tracing
   ```python
   response = await client.get("/endpoint", correlation_id=trace_id)
   ```

2. **Set consumer_id** to identify your service
   ```python
   config = HttpClientConfig(..., consumer_id="my-service-v1")
   ```

3. **Configure timeouts** appropriately
   ```python
   config = HttpClientConfig(..., timeout=30.0)
   ```

4. **Enable circuit breaker** for external services
   ```python
   config = HttpClientConfig(..., enable_circuit_breaker=True)
   ```

5. **Use retry logic** for transient failures
   ```python
   config = HttpClientConfig(..., retry_policy=ExponentialBackoff())
   ```

6. **Protect sensitive data** in logs
   ```python
   config = HttpClientConfig(..., log_request_body=False, log_response_body=False)
   ```

### ❌ Don'ts

1. **Don't log sensitive data** (passwords, tokens, payment info)
2. **Don't use infinite retries** - always set max_retries
3. **Don't ignore circuit breaker state** - handle CircuitBreakerError
4. **Don't share HttpClient instances** across different services
5. **Don't forget to close the client** - use `async with`
6. **Don't set timeout too low** - consider network latency

---

## 🔍 Troubleshooting

### Circuit Breaker Opens Frequently

**Problem:** Circuit breaker keeps opening

**Solutions:**
- Increase `circuit_breaker_failure_threshold`
- Increase `circuit_breaker_timeout`
- Check if downstream service is healthy
- Review error logs for root cause

```python
# Check circuit breaker stats
stats = client.get_circuit_breaker_stats()
print(f"State: {stats['state']}, Failures: {stats['failure_count']}")
```

### Timeout Errors

**Problem:** Requests timeout frequently

**Solutions:**
- Increase timeout value
- Check network latency
- Verify downstream service performance
- Consider using longer timeout for specific endpoints

```python
# Per-request timeout override
response = await client.get("/slow-endpoint", timeout=60.0)
```

### Authentication Failures

**Problem:** 401 Unauthorized errors

**Solutions:**
- Verify auth credentials are correct
- Check token expiration (OAuth2 auto-refreshes)
- Verify auth strategy type matches API requirements
- Check auth headers in logs

---

## 📚 Related Documentation

- [EXCEPTION_HANDLER.md](EXCEPTION_HANDLER.md) - Handle HTTP errors with ProblemDetails
- [OBSERVABILITY.md](OBSERVABILITY.md) - Tracing and monitoring
- [MEDIATOR_PATTERN.md](MEDIATOR_PATTERN.md) - Application layer patterns

---

## 🎓 Summary

The HTTP Client wrapper provides:

✅ **Production-Ready** - Retry, circuit breaker, timeouts  
✅ **Secure** - Multiple auth strategies, sensitive data protection  
✅ **Observable** - Tracing, logging, correlation IDs  
✅ **Efficient** - Connection pooling, HTTP/2 support  
✅ **Flexible** - Configurable for any external API  
✅ **Python-Idiomatic** - Async/await, context managers  

**Next Steps:**
1. Configure HttpClient for your external APIs
2. Enable tracing and logging
3. Set appropriate timeouts and retry policies
4. Monitor circuit breaker metrics
5. Test with demo_http_client.py
