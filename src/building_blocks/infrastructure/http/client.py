"""
HTTP Client Wrapper

Production-ready HTTP client for external API communication with:
- Multiple authentication strategies
- Automatic correlation ID and consumer ID injection
- Retry logic with exponential backoff
- Circuit breaker pattern
- Request/response logging
- OpenTelemetry tracing integration
- Timeout configuration
- Comprehensive error handling
"""

import logging
import uuid
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

import httpx
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from .auth import AuthStrategy, NoAuth
from .retry import RetryPolicy, ExponentialBackoff
from .circuit_breaker import CircuitBreaker, CircuitBreakerError

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


@dataclass
class HttpClientConfig:
    """Configuration for HTTP client."""
    
    # Base configuration
    base_url: str
    timeout: float = 30.0
    
    # Authentication
    auth_strategy: AuthStrategy = field(default_factory=NoAuth)
    
    # Retry configuration
    retry_policy: RetryPolicy = field(default_factory=lambda: ExponentialBackoff(max_retries=3))
    
    # Circuit breaker configuration
    enable_circuit_breaker: bool = True
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_timeout: float = 60.0
    
    # Headers
    consumer_id: Optional[str] = None
    default_headers: Dict[str, str] = field(default_factory=dict)
    
    # Logging
    log_requests: bool = True
    log_responses: bool = True
    log_request_body: bool = False  # Careful with sensitive data
    log_response_body: bool = False  # Careful with large responses
    
    # Tracing
    enable_tracing: bool = True
    
    # HTTP/2
    http2: bool = False
    
    # Limits
    max_connections: int = 100
    max_keepalive_connections: int = 20


class HttpClient:
    """
    Production-ready HTTP client wrapper.
    
    Features:
    - Automatic correlation ID (X-Correlation-Id) injection
    - Automatic consumer ID (X-Consumer-Id) injection
    - Multiple authentication strategies
    - Retry logic with exponential backoff
    - Circuit breaker pattern
    - Request/response logging
    - OpenTelemetry distributed tracing
    - Timeout configuration
    - Connection pooling
    """
    
    def __init__(self, config: HttpClientConfig):
        """
        Initialize HTTP client.
        
        Args:
            config: Client configuration
        """
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._circuit_breaker: Optional[CircuitBreaker] = None
        
        if config.enable_circuit_breaker:
            self._circuit_breaker = CircuitBreaker(
                failure_threshold=config.circuit_breaker_failure_threshold,
                timeout=config.circuit_breaker_timeout,
                expected_exception=httpx.HTTPError
            )
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_client(self) -> None:
        """Ensure HTTP client is initialized."""
        if self._client is None:
            limits = httpx.Limits(
                max_connections=self.config.max_connections,
                max_keepalive_connections=self.config.max_keepalive_connections
            )
            
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=httpx.Timeout(self.config.timeout),
                http2=self.config.http2,
                limits=limits,
                event_hooks={
                    "request": [self._log_request, self._apply_auth],
                    "response": [self._log_response]
                }
            )
    
    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    # ========================================================================
    # HTTP Methods
    # ========================================================================
    
    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
        **kwargs
    ) -> httpx.Response:
        """
        Perform GET request.
        
        Args:
            path: URL path (relative to base_url)
            params: Query parameters
            headers: Additional headers
            correlation_id: Optional correlation ID (generated if not provided)
            **kwargs: Additional arguments passed to httpx
            
        Returns:
            HTTP response
        """
        return await self.request(
            "GET",
            path,
            params=params,
            headers=headers,
            correlation_id=correlation_id,
            **kwargs
        )
    
    async def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
        **kwargs
    ) -> httpx.Response:
        """
        Perform POST request.
        
        Args:
            path: URL path
            json: JSON body
            data: Form data
            headers: Additional headers
            correlation_id: Optional correlation ID
            **kwargs: Additional arguments
            
        Returns:
            HTTP response
        """
        return await self.request(
            "POST",
            path,
            json=json,
            data=data,
            headers=headers,
            correlation_id=correlation_id,
            **kwargs
        )
    
    async def put(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
        **kwargs
    ) -> httpx.Response:
        """Perform PUT request."""
        return await self.request(
            "PUT",
            path,
            json=json,
            data=data,
            headers=headers,
            correlation_id=correlation_id,
            **kwargs
        )
    
    async def patch(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
        **kwargs
    ) -> httpx.Response:
        """Perform PATCH request."""
        return await self.request(
            "PATCH",
            path,
            json=json,
            data=data,
            headers=headers,
            correlation_id=correlation_id,
            **kwargs
        )
    
    async def delete(
        self,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
        **kwargs
    ) -> httpx.Response:
        """Perform DELETE request."""
        return await self.request(
            "DELETE",
            path,
            headers=headers,
            correlation_id=correlation_id,
            **kwargs
        )
    
    async def request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
        **kwargs
    ) -> httpx.Response:
        """
        Perform HTTP request with retry and circuit breaker.
        
        Args:
            method: HTTP method
            path: URL path
            headers: Additional headers
            correlation_id: Optional correlation ID
            **kwargs: Additional arguments passed to httpx
            
        Returns:
            HTTP response
            
        Raises:
            CircuitBreakerError: If circuit breaker is open
            httpx.HTTPError: For HTTP errors
        """
        await self._ensure_client()
        
        # Prepare headers
        request_headers = self._prepare_headers(headers, correlation_id)
        
        # Create span for tracing
        span_name = f"HTTP {method} {path}"
        
        if self.config.enable_tracing:
            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute("http.method", method)
                span.set_attribute("http.url", f"{self.config.base_url}{path}")
                span.set_attribute("correlation_id", request_headers.get("X-Correlation-Id", ""))
                
                try:
                    response = await self._execute_with_retry(
                        method, path, request_headers, **kwargs
                    )
                    span.set_attribute("http.status_code", response.status_code)
                    span.set_status(Status(StatusCode.OK))
                    return response
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        else:
            return await self._execute_with_retry(
                method, path, request_headers, **kwargs
            )
    
    async def _execute_with_retry(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        **kwargs
    ) -> httpx.Response:
        """Execute request with retry logic and circuit breaker."""
        attempt = 0
        last_exception = None
        last_response = None
        
        while True:
            try:
                # Check circuit breaker
                if self._circuit_breaker:
                    response = await self._circuit_breaker.call(
                        self._make_request,
                        method, path, headers, **kwargs
                    )
                else:
                    response = await self._make_request(
                        method, path, headers, **kwargs
                    )
                
                # Check if response should trigger retry
                if await self.config.retry_policy.should_retry(
                    attempt, response=response
                ):
                    last_response = response
                    attempt += 1
                    
                    wait_time = await self.config.retry_policy.get_wait_time(attempt - 1)
                    logger.warning(
                        f"Retrying request after {response.status_code} response. "
                        f"Attempt {attempt}, waiting {wait_time:.2f}s"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                
                return response
                
            except Exception as e:
                last_exception = e
                
                # Check if exception should trigger retry
                if await self.config.retry_policy.should_retry(attempt, exception=e):
                    attempt += 1
                    wait_time = await self.config.retry_policy.get_wait_time(attempt - 1)
                    logger.warning(
                        f"Retrying request after exception: {type(e).__name__}. "
                        f"Attempt {attempt}, waiting {wait_time:.2f}s"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                
                raise
    
    async def _make_request(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        **kwargs
    ) -> httpx.Response:
        """Make actual HTTP request."""
        response = await self._client.request(
            method, path, headers=headers, **kwargs
        )
        response.raise_for_status()
        return response
    
    def _prepare_headers(
        self,
        additional_headers: Optional[Dict[str, str]],
        correlation_id: Optional[str]
    ) -> Dict[str, str]:
        """Prepare request headers with correlation ID and consumer ID."""
        headers = {**self.config.default_headers}
        
        # Add correlation ID
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        headers["X-Correlation-Id"] = correlation_id
        
        # Add consumer ID
        if self.config.consumer_id:
            headers["X-Consumer-Id"] = self.config.consumer_id
        
        # Add additional headers
        if additional_headers:
            headers.update(additional_headers)
        
        return headers
    
    # ========================================================================
    # Event Hooks
    # ========================================================================
    
    async def _apply_auth(self, request: httpx.Request) -> None:
        """Apply authentication to request."""
        await self.config.auth_strategy.refresh_if_needed()
        await self.config.auth_strategy.apply_auth(request)
    
    async def _log_request(self, request: httpx.Request) -> None:
        """Log outgoing request."""
        if not self.config.log_requests:
            return
        
        log_data = {
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "correlation_id": request.headers.get("X-Correlation-Id"),
        }
        
        if self.config.log_request_body and request.content:
            log_data["body"] = request.content.decode("utf-8", errors="replace")[:1000]
        
        logger.info(f"HTTP Request: {request.method} {request.url}", extra=log_data)
    
    async def _log_response(self, response: httpx.Response) -> None:
        """Log incoming response."""
        if not self.config.log_responses:
            return
        
        log_data = {
            "method": response.request.method,
            "url": str(response.request.url),
            "status_code": response.status_code,
            "correlation_id": response.request.headers.get("X-Correlation-Id"),
        }
        
        if self.config.log_response_body:
            try:
                log_data["body"] = response.text[:1000]
            except Exception:
                pass
        
        log_level = logging.INFO if response.is_success else logging.WARNING
        logger.log(
            log_level,
            f"HTTP Response: {response.status_code} for {response.request.method} {response.request.url}",
            extra=log_data
        )
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def get_circuit_breaker_stats(self) -> Optional[dict]:
        """Get circuit breaker statistics."""
        if self._circuit_breaker:
            return self._circuit_breaker.get_stats()
        return None
    
    async def reset_circuit_breaker(self) -> None:
        """Manually reset circuit breaker."""
        if self._circuit_breaker:
            await self._circuit_breaker.reset()


# Import asyncio at the top (forgot to add)
import asyncio
