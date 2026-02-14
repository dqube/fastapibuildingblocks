"""
HTTP Client Infrastructure

Provides a robust HTTP client wrapper for external API communication with:
- Multiple authentication strategies
- Automatic correlation ID and consumer ID injection
- Retry logic with exponential backoff
- Circuit breaker pattern
- Request/response logging
- OpenTelemetry tracing integration
"""

from .auth import (
    AuthStrategy,
    NoAuth,
    BearerAuth,
    BasicAuth,
    ApiKeyAuth,
    OAuth2ClientCredentials,
    CustomHeaderAuth,
)
from .client import HttpClient, HttpClientConfig
from .retry import RetryPolicy, ExponentialBackoff, NoRetry
from .circuit_breaker import CircuitBreaker, CircuitBreakerState

__all__ = [
    # Client
    "HttpClient",
    "HttpClientConfig",
    
    # Auth
    "AuthStrategy",
    "NoAuth",
    "BearerAuth",
    "BasicAuth",
    "ApiKeyAuth",
    "OAuth2ClientCredentials",
    "CustomHeaderAuth",
    
    # Retry
    "RetryPolicy",
    "ExponentialBackoff",
    "NoRetry",
    
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerState",
]
