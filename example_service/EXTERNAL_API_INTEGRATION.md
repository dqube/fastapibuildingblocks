# External API Integration

This document describes the external API integration feature that allows calling external APIs with configuration-based authentication and resilience patterns.

## Overview

The External API integration provides endpoints to:
- Call external APIs with configured service settings
- Support multiple authentication types
- Manage service configurations (CRUD operations)
- Apply retry policies and circuit breaker patterns
- Track requests with correlation IDs and consumer IDs

## Architecture

### Components

1. **External API Endpoints** (`app/api/v1/endpoints/external_api.py`)
   - API endpoints for calling external services
   - Service configuration management (CRUD)
   - Quick test endpoints

2. **HTTP Client** (`building_blocks/infrastructure/http/client.py`)
   - Async HTTP client with httpx
   - authentication strategy injection
   - Retry policies and circuit breaker
   - Request/response logging and tracing

3. **Authentication Strategies** (`building_blocks/infrastructure/http/auth.py`)
   - NoAuth: No authentication
   - BearerAuth: Bearer token (OAuth2, API tokens)
   - BasicAuth: HTTP Basic Authentication
   - ApiKeyAuth: API key in custom header
   - OAuth2ClientCredentials: OAuth2 client credentials flow
   - CustomHeaderAuth: Custom authentication headers
   - DigestAuth: HTTP Digest Authentication

## API Endpoints

### Service Configuration Management

#### List All Services
```http
GET /api/v1/external-api/services
```

Returns all configured external services (without sensitive credentials).

**Response:**
```json
{
  "jsonplaceholder": {
    "name": "jsonplaceholder",
    "base_url": "https://jsonplaceholder.typicode.com/",
    "auth_type": "none",
    "timeout": 15.0,
    "max_retries": 3,
    "consumer_id": "user-management-api",
    "has_credentials": false
  },
  "github": {
    "name": "github",
    "base_url": "https://api.github.com/",
    "auth_type": "bearer",
    "timeout": 30.0,
    "max_retries": 3,
    "consumer_id": "user-management-api",
    "has_credentials": true
  }
}
```

#### Get Service Configuration
```http
GET /api/v1/external-api/services/{service_name}
```

Returns configuration for a specific service.

#### Add New Service
```http
POST /api/v1/external-api/services
Content-Type: application/json

{
  "name": "weatherapi",
  "base_url": "https://api.weatherapi.com/v1",
  "auth_type": "api_key",
  "api_key": "your_api_key_here",
  "api_key_header": "key",
  "timeout": 15.0,
  "max_retries": 2,
  "consumer_id": "weather-service"
}
```

#### Update Service
```http
PUT /api/v1/external-api/services/{service_name}
Content-Type: application/json

{
  "name": "weatherapi",
  "base_url": "https://api.weatherapi.com/v1",
  "auth_type": "api_key",
  "api_key": "updated_api_key",
  "api_key_header": "key",
  "timeout": 20.0,
  "max_retries": 3,
  "consumer_id": "weather-service"
}
```

#### Delete Service
```http
DELETE /api/v1/external-api/services/{service_name}
```

### Generic API Call

#### Call External API
```http
POST /api/v1/external-api/call
Content-Type: application/json

{
  "service_name": "jsonplaceholder",
  "method": "GET",
  "endpoint": "/posts/1",
  "query_params": {
    "_limit": "5"
  },
  "headers": {
    "Custom-Header": "value"
  },
  "body": {
    "title": "My Post",
    "body": "Post content"
  }
}
```

**Response:**
```json
{
  "success": true,
  "status_code": 200,
  "data": {
    "userId": 1,
    "id": 1,
    "title": "sunt aut facere repellat provident occaecati excepturi optio reprehenderit",
    "body": "quia et suscipit..."
  },
  "headers": {
    "content-type": "application/json; charset=utf-8",
    "x-ratelimit-limit": "1000",
    "x-ratelimit-remaining": "999"
  },
  "service_name": "jsonplaceholder",
  "endpoint": "/posts/1",
  "correlation_id": "abc123-def456"
}
```

### Quick Test Endpoints

#### Test JSONPlaceholder (No Auth)
```http
GET /api/v1/external-api/test/jsonplaceholder
```

Gets posts from JSONPlaceholder API (public, no authentication).

#### Test GitHub User (Bearer Auth)
```http
GET /api/v1/external-api/test/github/user
```

Gets authenticated GitHub user (requires valid Bearer token in config).

#### Create Post on JSONPlaceholder
```http
POST /api/v1/external-api/test/jsonplaceholder/post?title=Test&body=Content
```

Creates a post on JSONPlaceholder API.

## Configuration

### Pre-configured Services

The following services are pre-configured (you need to add real API keys):

1. **JSONPlaceholder** (No Auth)
   - Base URL: `https://jsonplaceholder.typicode.com`
   - For testing and demonstration

2. **GitHub** (Bearer Token)
   - Base URL: `https://api.github.com`
   - Requires: GitHub personal access token

3. **Stripe** (Bearer Token)
   - Base URL: `https://api.stripe.com/v1`
   - Requires: Stripe API key

4. **SendGrid** (Bearer Token)
   - Base URL: `https://api.sendgrid.com/v3`
   - Requires: SendGrid API key

### Service Configuration Schema

```typescript
{
  "name": string,              // Unique service identifier
  "base_url": string,          // Service base URL
  "auth_type": "none" | "bearer" | "basic" | "api_key" | "oauth2",
  
  // Bearer Token Auth
  "bearer_token"?: string,
  
  // Basic Auth
  "username"?: string,
  "password"?: string,
  
  // API Key Auth
  "api_key"?: string,
  "api_key_header"?: string,   // Default: "X-API-Key"
  
  // OAuth2 Client Credentials
  "oauth2_token_url"?: string,
  "oauth2_client_id"?: string,
  "oauth2_client_secret"?: string,
  "oauth2_scope"?: string,
  
  // Additional Settings
  "timeout": float,            // Request timeout (seconds)
  "max_retries": int,          // Maximum retry attempts
  "consumer_id"?: string       // Consumer ID for tracking
}
```

## Authentication Types

### 1. No Authentication
```json
{
  "name": "public-api",
  "base_url": "https://api.example.com",
  "auth_type": "none"
}
```

### 2. Bearer Token
Used for:
- OAuth2 access tokens
- API tokens (GitHub, Stripe, SendGrid)

```json
{
  "name": "github",
  "base_url": "https://api.github.com",
  "auth_type": "bearer",
  "bearer_token": "ghp_xxxxxxxxxxxxx"
}
```

HTTP Header:
```
Authorization: Bearer ghp_xxxxxxxxxxxxx
```

### 3. Basic Authentication
```json
{
  "name": "basic-auth-api",
  "base_url": "https://api.example.com",
  "auth_type": "basic",
  "username": "admin",
  "password": "secret"
}
```

HTTP Header:
```
Authorization: Basic YWRtaW46c2VjcmV0
```

### 4. API Key
```json
{
  "name": "weather-api",
  "base_url": "https://api.weatherapi.com/v1",
  "auth_type": "api_key",
  "api_key": "your_api_key",
  "api_key_header": "X-API-Key"
}
```

HTTP Header:
```
X-API-Key: your_api_key
```

### 5. OAuth2 Client Credentials
```json
{
  "name": "oauth-api",
  "base_url": "https://api.example.com",
  "auth_type": "oauth2",
  "oauth2_token_url": "https://auth.example.com/oauth/token",
  "oauth2_client_id": "client_id",
  "oauth2_client_secret": "client_secret",
  "oauth2_scope": "read write"
}
```

## Features

### 1. Config-Based Service Management
- All service URLs and auth details read from configuration
- No hardcoding of credentials in code
- Easy to add/update/remove services at runtime

### 2. Multiple Authentication Strategies
- Support for 7 different authentication types
- Automatic credential injection
- Token refresh for OAuth2

### 3. Resilience Patterns

#### Retry Policy
```python
# Exponential backoff with jitter
max_retries: 3
base_delay: 1.0 seconds
max_delay: 60.0 seconds
```

#### Circuit Breaker
```python
failure_threshold: 5       # Trips after 5 failures
timeout: 60 seconds        # Open state duration
expected_exception: HTTPError
```

### 4. Request Tracking

#### Correlation ID
- Automatically generated for each request
- Propagated to external services
- Included in response for tracing

#### Consumer ID
- Identifies the calling service
- Used for rate limiting and tracking
- Configurable per service

### 5. Logging and Observability
- Request logging (method, URL, headers, body)
- Response logging (status, headers, body)
- Automatic redaction of sensitive data (passwords, tokens, API keys)
- OpenTelemetry tracing integration

## Usage Examples

### Example 1: Call Public API (No Auth)
```bash
curl -X POST http://localhost:8000/api/v1/external-api/call \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "jsonplaceholder",
    "method": "GET",
    "endpoint": "/posts",
    "query_params": {"_limit": "5"}
  }'
```

### Example 2: Create Resource via API
```bash
curl -X POST http://localhost:8000/api/v1/external-api/call \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "jsonplaceholder",
    "method": "POST",
    "endpoint": "/posts",
    "body": {
      "title": "My New Post",
      "body": "Post content",
      "userId": 1
    }
  }'
```

### Example 3: Update Resource
```bash
curl -X POST http://localhost:8000/api/v1/external-api/call \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "jsonplaceholder",
    "method": "PUT",
    "endpoint": "/posts/1",
    "body": {
      "id": 1,
      "title": "Updated Title",
      "body": "Updated content",
      "userId": 1
    }
  }'
```

### Example 4: Delete Resource
```bash
curl -X POST http://localhost:8000/api/v1/external-api/call \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "jsonplaceholder",
    "method": "DELETE",
    "endpoint": "/posts/1"
  }'
```

### Example 5: Add New Service Configuration
```bash
curl -X POST http://localhost:8000/api/v1/external-api/services \
  -H "Content-Type: application/json" \
  -d '{
    "name": "myapi",
    "base_url": "https://api.myservice.com",
    "auth_type": "bearer",
    "bearer_token": "my_api_token",
    "timeout": 30.0,
    "max_retries": 3,
    "consumer_id": "my-service"
  }'
```

## Testing

Run the comprehensive test script:
```bash
cd example_service
./test_external_api.sh
```

The test script validates:
1. ✅ Service configuration management (CRUD)
2. ✅ No authentication (JSONPlaceholder)
3. ✅ Bearer token authentication (GitHub, Stripe, SendGrid)
4. ✅ API key authentication (custom service)
5. ✅ All HTTP methods (GET, POST, PUT, PATCH, DELETE)
6. ✅ Query parameters
7. ✅ Request body support
8. ✅ Error handling
9. ✅ Correlation ID injection
10. ✅ Consumer ID tracking

## Security Considerations

### 1. Credential Storage
- **Current**: In-memory storage (demo only)
- **Production**: Use secure storage:
  - Database with encryption
  - Secrets management service (AWS Secrets Manager, Azure Key Vault)
  - Environment variables (for non-rotating secrets)

### 2. Sensitive Data Redaction
- Automatic redaction in logs:
  - Passwords: `***REDACTED***(length)`
  - Tokens: `***REDACTED***(length)`
  - API keys: `***REDACTED***(length)`

### 3. HTTPS Enforcement
- All external API calls should use HTTPS
- HTTP/2 support enabled by default

### 4. Rate Limiting
- Respect external API rate limits
- Implement client-side rate limiting if needed
- Track remaining rate limit from headers

## API Documentation

Interactive API documentation available at:
- Swagger UI: http://localhost:8000/docs#/external-api
- ReDoc: http://localhost:8000/redoc

## Environment Configuration

For production use, configure services via environment variables:

```bash
# GitHub API
GITHUB_API_TOKEN=ghp_xxxxxxxxxxxxx

# Stripe API
STRIPE_API_KEY=sk_live_xxxxxxxxxxxxx

# SendGrid API
SENDGRID_API_KEY=SG.xxxxxxxxxxxxx

# Custom API
CUSTOM_API_URL=https://api.example.com
CUSTOM_API_KEY=xxxxxxxxxxxxx
```

Then load from environment in code:
```python
import os

github_service = ExternalServiceConfig(
    name="github",
    base_url="https://api.github.com",
    auth_type=AuthType.BEARER,
    bearer_token=os.getenv("GITHUB_API_TOKEN"),
    timeout=30.0,
    consumer_id="my-service"
)
```

## Best Practices

### 1. Use Appropriate Timeouts
- Short-lived requests (< 5s): `timeout=5.0`
- Standard requests: `timeout=15.0` (default)
- Long-running requests (uploads, etc.): `timeout=60.0`

### 2. Set Reasonable Retry Counts
- Critical operations: `max_retries=5`
- Standard operations: `max_retries=3` (default)
- Non-critical operations: `max_retries=1`

### 3. Track Consumer IDs
- Use service name as consumer_id
- Include in all outgoing requests
- Track per-consumer metrics

### 4. Handle Rate Limits
- Check `x-ratelimit-*` headers in responses
- Implement backoff if approaching limit
- Use circuit breaker to prevent excessive calls

### 5. Monitor Circuit Breaker
- Alert when circuit opens
- Track failure rates
- Adjust thresholds based on service SLAs

## Troubleshooting

### Issue: Authentication Failures

**Symptoms:**
- 401 Unauthorized responses
- "Invalid credentials" errors

**Solutions:**
1. Verify API key/token is correct and not expired
2. Check auth_type matches service requirements
3. Verify header name for API key authentication
4. Test credentials directly with curl/Postman

### Issue: Timeout Errors

**Symptoms:**
- Requests timing out
- "Connection timeout" errors

**Solutions:**
1. Increase timeout value
2. Check network connectivity
3. Verify service URL is correct
4. Check if service is rate limiting

### Issue: Circuit Breaker Open

**Symptoms:**
- "Circuit breaker is open" errors
- Service unavailable messages

**Solutions:**
1. Wait for circuit breaker timeout (60s default)
2. Check external service health
3. Review failure threshold settings
4. Implement fallback logic

## Future Enhancements

1. **Persistent Configuration Storage**
   - Store service configs in database
   - Version control for configurations
   - Audit trail

2. **Advanced Rate Limiting**
   - Token bucket algorithm
   - Sliding window rate limiting
   - Per-service rate limits

3. **Caching Layer**
   - Cache GET responses
   - TTL-based cache invalidation
   - Cache key strategies

4. **Webhook Support**
   - Register webhooks with external services
   - Handle incoming webhook events
   - Verify webhook signatures

5. **GraphQL Support**
   - GraphQL query execution
   - Schema validation
   - Query optimization

## Related Documentation

- [HTTP Client Architecture](../src/building_blocks/infrastructure/http/README.md)
- [Authentication Strategies](../src/building_blocks/infrastructure/http/auth.py)
- [Retry Policies](../src/building_blocks/infrastructure/http/retry.py)
- [Circuit Breaker Pattern](../src/building_blocks/infrastructure/http/circuit_breaker.py)
