"""
External API Integration Endpoints

Demonstrates calling external APIs using the HTTP client wrapper with configuration-based authentication.
Supports multiple authentication types and service configurations.
"""

from typing import Any, Dict, Optional, List
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum
import logging

logger = logging.getLogger(__name__)

from building_blocks.infrastructure.http import (
    HttpClient,
    HttpClientConfig,
    BearerAuth,
    BasicAuth,
    ApiKeyAuth,
    OAuth2ClientCredentials,
)

router = APIRouter()


# ==================== Models ====================

class AuthType(str, Enum):
    """Supported authentication types."""
    NONE = "none"
    BEARER = "bearer"
    BASIC = "basic"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"


class ExternalServiceConfig(BaseModel):
    """External service configuration."""
    name: str = Field(..., description="Service name")
    base_url: HttpUrl = Field(..., description="Base URL of the service")
    auth_type: AuthType = Field(default=AuthType.NONE, description="Authentication type")
    
    # Bearer token auth
    bearer_token: Optional[str] = Field(None, description="Bearer token")
    
    # Basic auth
    username: Optional[str] = Field(None, description="Basic auth username")
    password: Optional[str] = Field(None, description="Basic auth password")
    
    # API key auth
    api_key: Optional[str] = Field(None, description="API key")
    api_key_header: str = Field(default="X-API-Key", description="API key header name")
    
    # OAuth2 client credentials
    oauth2_token_url: Optional[str] = Field(None, description="OAuth2 token URL")
    oauth2_client_id: Optional[str] = Field(None, description="OAuth2 client ID")
    oauth2_client_secret: Optional[str] = Field(None, description="OAuth2 client secret")
    oauth2_scope: Optional[str] = Field(None, description="OAuth2 scope")
    
    # Additional settings
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    consumer_id: Optional[str] = Field(None, description="Consumer ID for tracking")


class ApiCallRequest(BaseModel):
    """API call request."""
    service_name: str = Field(..., description="Configured service name")
    method: str = Field(..., description="HTTP method (GET, POST, PUT, DELETE, PATCH)")
    endpoint: str = Field(..., description="API endpoint path (e.g., /users/123)")
    headers: Optional[Dict[str, str]] = Field(None, description="Additional headers")
    query_params: Optional[Dict[str, Any]] = Field(None, description="Query parameters")
    body: Optional[Dict[str, Any]] = Field(None, description="Request body (for POST/PUT/PATCH)")


class ApiCallResponse(BaseModel):
    """API call response."""
    success: bool
    status_code: int
    data: Optional[Any] = None
    headers: Optional[Dict[str, str]] = None
    error: Optional[str] = None
    service_name: str
    endpoint: str
    correlation_id: Optional[str] = None


# ==================== Configuration Storage ====================

# In-memory storage for demo (in production, use database or config service)
_external_services: Dict[str, ExternalServiceConfig] = {
    # Example configurations
    "github": ExternalServiceConfig(
        name="github",
        base_url="https://api.github.com",
        auth_type=AuthType.BEARER,
        bearer_token="ghp_your_github_token_here",
        timeout=30.0,
        max_retries=3,
        consumer_id="user-management-api"
    ),
    "jsonplaceholder": ExternalServiceConfig(
        name="jsonplaceholder",
        base_url="https://jsonplaceholder.typicode.com",
        auth_type=AuthType.NONE,
        timeout=15.0,
        consumer_id="user-management-api"
    ),
    "stripe": ExternalServiceConfig(
        name="stripe",
        base_url="https://api.stripe.com/v1",
        auth_type=AuthType.BEARER,
        bearer_token="sk_test_your_stripe_key",
        timeout=30.0,
        consumer_id="payment-service"
    ),
    "sendgrid": ExternalServiceConfig(
        name="sendgrid",
        base_url="https://api.sendgrid.com/v3",
        auth_type=AuthType.BEARER,
        bearer_token="SG.your_sendgrid_api_key",
        timeout=20.0,
        consumer_id="notification-service"
    ),
}


def _get_auth_strategy(config: ExternalServiceConfig):
    """Create auth strategy from configuration."""
    if config.auth_type == AuthType.BEARER:
        if not config.bearer_token:
            raise ValueError(f"Bearer token required for service: {config.name}")
        return BearerAuth(token=config.bearer_token)
    
    elif config.auth_type == AuthType.BASIC:
        if not config.username or not config.password:
            raise ValueError(f"Username and password required for service: {config.name}")
        return BasicAuth(username=config.username, password=config.password)
    
    elif config.auth_type == AuthType.API_KEY:
        if not config.api_key:
            raise ValueError(f"API key required for service: {config.name}")
        return ApiKeyAuth(api_key=config.api_key, header_name=config.api_key_header)
    
    elif config.auth_type == AuthType.OAUTH2:
        if not all([config.oauth2_token_url, config.oauth2_client_id, config.oauth2_client_secret]):
            raise ValueError(f"OAuth2 credentials required for service: {config.name}")
        return OAuth2ClientCredentials(
            token_url=config.oauth2_token_url,
            client_id=config.oauth2_client_id,
            client_secret=config.oauth2_client_secret,
            scope=config.oauth2_scope
        )
    
    else:  # AuthType.NONE
        from building_blocks.infrastructure.http.auth import NoAuth
        return NoAuth()


async def _create_http_client(config: ExternalServiceConfig) -> HttpClient:
    """Create HTTP client from service configuration."""
    auth_strategy = _get_auth_strategy(config)
    
    from building_blocks.infrastructure.http.retry import ExponentialBackoff
    
    client_config = HttpClientConfig(
        base_url=str(config.base_url),
        timeout=config.timeout,
        auth_strategy=auth_strategy,
        retry_policy=ExponentialBackoff(max_retries=config.max_retries),
        consumer_id=config.consumer_id or config.name,
        enable_circuit_breaker=True,
        log_requests=True,
        log_responses=True,
    )
    
    return HttpClient(client_config)


# ==================== Endpoints ====================

@router.post("/call", response_model=ApiCallResponse, status_code=status.HTTP_200_OK)
async def call_external_api(request: ApiCallRequest):
    """
    Call an external API using configured service settings.
    
    This endpoint demonstrates:
    - Reading service configuration
    - Creating HTTP client with appropriate auth
    - Making API calls with retry and circuit breaker
    - Automatic correlation ID injection
    - Request/response logging
    
    **Example services available:**
    - `github` - GitHub API (Bearer token auth)
    - `jsonplaceholder` - JSONPlaceholder (No auth, for testing)
    - `stripe` - Stripe API (Bearer token auth)
    - `sendgrid` - SendGrid API (Bearer token auth)
    """
    # Get service configuration
    service_config = _external_services.get(request.service_name)
    if not service_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{request.service_name}' not found. "
                   f"Available services: {list(_external_services.keys())}"
        )
    
    # Create HTTP client with service configuration
    client = await _create_http_client(service_config)
    
    try:
        # Use async context manager
        async with client:
            # Prepare request parameters
            method = request.method.upper()
            endpoint = request.endpoint
            
            # Make the API call
            if method == "GET":
                response = await client.get(
                    endpoint,
                    params=request.query_params,
                    headers=request.headers
                )
            elif method == "POST":
                response = await client.post(
                    endpoint,
                    json=request.body,
                    params=request.query_params,
                    headers=request.headers
                )
            elif method == "PUT":
                response = await client.put(
                    endpoint,
                    json=request.body,
                    params=request.query_params,
                    headers=request.headers
                )
            elif method == "PATCH":
                response = await client.patch(
                    endpoint,
                    json=request.body,
                    params=request.query_params,
                    headers=request.headers
                )
            elif method == "DELETE":
                response = await client.delete(
                    endpoint,
                    params=request.query_params,
                    headers=request.headers
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported HTTP method: {method}"
                )
            
            # Parse response
            try:
                data = response.json()
            except Exception:
                data = response.text
            
            return ApiCallResponse(
                success=True,
                status_code=response.status_code,
                data=data,
                headers=dict(response.headers),
                service_name=request.service_name,
                endpoint=endpoint,
                correlation_id=response.headers.get("x-correlation-id")
            )
    
    except Exception as e:
        logger.error(f"Error calling external API: {str(e)}")
        return ApiCallResponse(
            success=False,
            status_code=500,
            error=str(e),
            service_name=request.service_name,
            endpoint=request.endpoint
        )


@router.get("/services", response_model=Dict[str, Dict[str, Any]])
async def list_services():
    """
    List all configured external services.
    
    Returns service configurations (without sensitive data like tokens).
    """
    services = {}
    for name, config in _external_services.items():
        services[name] = {
            "name": config.name,
            "base_url": str(config.base_url),
            "auth_type": config.auth_type,
            "timeout": config.timeout,
            "max_retries": config.max_retries,
            "consumer_id": config.consumer_id,
            # Don't expose sensitive data
            "has_credentials": config.auth_type != AuthType.NONE
        }
    return services


@router.post("/services", response_model=Dict[str, str], status_code=status.HTTP_201_CREATED)
async def add_service(config: ExternalServiceConfig):
    """
    Add a new external service configuration.
    
    **Note:** In production, store this in a database or secure config service.
    """
    if config.name in _external_services:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Service '{config.name}' already exists"
        )
    
    _external_services[config.name] = config
    return {"message": f"Service '{config.name}' added successfully"}


@router.put("/services/{service_name}", response_model=Dict[str, str])
async def update_service(service_name: str, config: ExternalServiceConfig):
    """
    Update an existing external service configuration.
    """
    if service_name not in _external_services:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_name}' not found"
        )
    
    config.name = service_name  # Ensure name matches
    _external_services[service_name] = config
    return {"message": f"Service '{service_name}' updated successfully"}


@router.delete("/services/{service_name}", response_model=Dict[str, str])
async def delete_service(service_name: str):
    """
    Delete an external service configuration.
    """
    if service_name not in _external_services:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_name}' not found"
        )
    
    del _external_services[service_name]
    return {"message": f"Service '{service_name}' deleted successfully"}


@router.get("/services/{service_name}", response_model=Dict[str, Any])
async def get_service(service_name: str):
    """
    Get configuration for a specific service (without sensitive data).
    """
    if service_name not in _external_services:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_name}' not found"
        )
    
    config = _external_services[service_name]
    return {
        "name": config.name,
        "base_url": str(config.base_url),
        "auth_type": config.auth_type,
        "timeout": config.timeout,
        "max_retries": config.max_retries,
        "consumer_id": config.consumer_id,
        "has_credentials": config.auth_type != AuthType.NONE
    }


# ==================== Quick Test Endpoints ====================

@router.get("/test/jsonplaceholder", response_model=ApiCallResponse)
async def test_jsonplaceholder():
    """
    Quick test endpoint - Get posts from JSONPlaceholder (public API, no auth).
    
    Demonstrates calling external API with no authentication.
    """
    request = ApiCallRequest(
        service_name="jsonplaceholder",
        method="GET",
        endpoint="/posts",
        query_params={"_limit": "5"}
    )
    return await call_external_api(request)


@router.get("/test/github/user", response_model=ApiCallResponse)
async def test_github_user():
    """
    Quick test endpoint - Get authenticated GitHub user.
    
    Demonstrates calling external API with Bearer token authentication.
    
    **Note:** Requires valid GitHub token in configuration.
    """
    request = ApiCallRequest(
        service_name="github",
        method="GET",
        endpoint="/user"
    )
    return await call_external_api(request)


@router.post("/test/jsonplaceholder/post", response_model=ApiCallResponse)
async def test_create_post(title: str = Query(...), body: str = Query(...)):
    """
    Quick test endpoint - Create a post on JSONPlaceholder.
    
    Demonstrates POST request with JSON body.
    """
    request = ApiCallRequest(
        service_name="jsonplaceholder",
        method="POST",
        endpoint="/posts",
        body={
            "title": title,
            "body": body,
            "userId": 1
        }
    )
    return await call_external_api(request)
