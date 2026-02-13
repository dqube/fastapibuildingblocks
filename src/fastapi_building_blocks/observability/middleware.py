"""
FastAPI middleware for automatic observability instrumentation.
"""

import time
import json
from typing import Callable, Optional, Dict, Any
from io import BytesIO

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse, StreamingResponse

from .config import ObservabilityConfig
from .tracing import setup_tracing, instrument_fastapi, get_tracer
from .logging import setup_logging, get_logger
from .metrics import setup_metrics, get_metrics
from .redaction import RedactionFilter, create_redaction_filter


logger = get_logger(__name__)
_observability_config: Optional[ObservabilityConfig] = None
_redaction_filter: Optional[RedactionFilter] = None


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically instrument HTTP requests with observability.
    
    Similar to ASP.NET Core middleware, logs request/response with:
    - Redacted request headers and body
    - Redacted response headers and body
    - Execution time in seconds and milliseconds
    - HTTP method, path, status code
    """
    
    async def _extract_request_data(self, request: Request) -> Dict[str, Any]:
        """
        Extract request data for logging.
        
        Args:
            request: HTTP request
            
        Returns:
            Dictionary of request data
        """
        data: Dict[str, Any] = {}
        config = _observability_config
        
        if not config:
            return data
        
        # Extract headers if enabled
        if config.log_request_headers:
            data["headers"] = dict(request.headers)
        
        # Extract body if enabled
        if config.log_request_body:
            try:
                # Read the body
                body = await request.body()
                
                # Check size limit
                if len(body) <= config.max_body_log_size:
                    # Try to parse as JSON
                    try:
                        data["body"] = json.loads(body.decode("utf-8"))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        # Store as string if not JSON
                        data["body"] = body.decode("utf-8", errors="replace")[:config.max_body_log_size]
                else:
                    data["body"] = f"<body too large: {len(body)} bytes>"
                
            except Exception as e:
                data["body_error"] = f"Failed to read body: {str(e)}"
        
        # Extract query parameters
        if request.query_params:
            data["query_params"] = dict(request.query_params)
        
        return data
    
    async def _extract_response_data(self, response: StarletteResponse) -> Dict[str, Any]:
        """
        Extract response data for logging.
        
        Args:
            response: HTTP response
            
        Returns:
            Dictionary of response data
        """
        data: Dict[str, Any] = {}
        config = _observability_config
        
        if not config:
            return data
        
        # Extract headers if enabled
        if config.log_response_headers:
            data["headers"] = dict(response.headers)
        
        # Extract body if enabled (only for non-streaming responses)
        if config.log_response_body and hasattr(response, "body"):
            try:
                body = response.body
                if len(body) <= config.max_body_log_size:
                    try:
                        data["body"] = json.loads(body.decode("utf-8"))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        data["body"] = body.decode("utf-8", errors="replace")[:config.max_body_log_size]
                else:
                    data["body"] = f"<body too large: {len(body)} bytes>"
            except Exception as e:
                data["body_error"] = f"Failed to read body: {str(e)}"
        
        return data
    
    def _should_log_details(self, path: str) -> bool:
        """
        Check if path should have detailed logging.
        
        Args:
            path: Request path
            
        Returns:
            True if should log details
        """
        if not _observability_config:
            return False
        
        # Check if path is in exclude list
        for exclude_path in _observability_config.exclude_paths:
            if path.startswith(exclude_path):
                return False
        
        return True
    
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        """
        Process HTTP request and add observability instrumentation.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler
            
        Returns:
            HTTP response
        """
        metrics = get_metrics()
        config = _observability_config
        
        # Extract request details
        method = request.method
        path = request.url.path
        should_log_details = self._should_log_details(path)
        
        # Track in-progress requests
        if metrics:
            metrics.http_requests_in_progress.labels(method=method, endpoint=path).inc()
        
        # Record start time
        start_time = time.time()
        
        # Extract request data if detailed logging is enabled
        request_data = {}
        if should_log_details and config and (config.log_request_body or config.log_request_headers):
            request_data = await self._extract_request_data(request)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            
            if metrics:
                metrics.http_requests_total.labels(
                    method=method,
                    endpoint=path,
                    status=response.status_code,
                ).inc()
                
                metrics.http_request_duration_seconds.labels(
                    method=method,
                    endpoint=path,
                ).observe(duration)
            
            # Extract response data if detailed logging is enabled
            response_data = {}
            if should_log_details and config and (config.log_response_body or config.log_response_headers):
                response_data = await self._extract_response_data(response)
            
            # Prepare log data
            log_data = {
                "http.method": method,
                "http.path": path,
                "http.status_code": response.status_code,
                "http.duration_seconds": round(duration, 4),
                "http.duration_ms": round(duration * 1000, 2),
            }
            
            # Add request data
            if request_data:
                log_data["http.request"] = request_data
            
            # Add response data
            if response_data:
                log_data["http.response"] = response_data
            
            # Apply redaction if enabled
            if _redaction_filter and config and config.log_redaction_enabled:
                log_data = _redaction_filter.redact_dict(log_data)
            
            # Create detailed log message with structured data embedded
            import json
            log_message = f"{method} {path} - {response.status_code} - {round(duration * 1000, 2)}ms | {json.dumps(log_data)}"
            
            # Log request with fields in both message and extra for flexibility
            logger.info(
                log_message,
                extra={"extra_fields": log_data},
            )
            
            return response
            
        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            
            if metrics:
                metrics.http_requests_total.labels(
                    method=method,
                    endpoint=path,
                    status=500,
                ).inc()
                
                metrics.http_request_duration_seconds.labels(
                    method=method,
                    endpoint=path,
                ).observe(duration)
            
            # Prepare error log data
            log_data = {
                "http.method": method,
                "http.path": path,
                "http.error_type": type(e).__name__,
                "http.duration_seconds": round(duration, 4),
                "http.duration_ms": round(duration * 1000, 2),
            }
            
            # Add request data if available
            if request_data:
                log_data["http.request"] = request_data
            
            # Apply redaction if enabled
            if _redaction_filter and config and config.log_redaction_enabled:
                log_data = _redaction_filter.redact_dict(log_data)
            
            # Log error
            logger.error(
                f"{method} {path} - ERROR: {str(e)} - {round(duration * 1000, 2)}ms",
                exc_info=True,
                extra={"extra_fields": log_data},
            )
            
            raise
            
        finally:
            # Decrement in-progress counter
            if metrics:
                metrics.http_requests_in_progress.labels(method=method, endpoint=path).dec()


def setup_observability(app: FastAPI, config: ObservabilityConfig) -> None:
    """
    Configure all observability features for a FastAPI application.
    
    This is a convenience function that sets up tracing, logging, metrics,
    and adds the observability middleware.
    
    Similar to ASP.NET Core middleware, this will log HTTP requests/responses
    with redacted sensitive data and execution time.
    
    Args:
        app: FastAPI application instance
        config: Observability configuration
        
    Example:
        from fastapi import FastAPI
        from fastapi_building_blocks.observability import setup_observability, ObservabilityConfig
        
        app = FastAPI()
        config = ObservabilityConfig(
            service_name="my-service",
            log_request_body=True,  # Log request bodies with redaction
            log_response_body=True,  # Log response bodies with redaction
            log_redaction_enabled=True,  # Enable sensitive data masking
        )
        setup_observability(app, config)
    """
    global _observability_config, _redaction_filter
    
    # Store config globally for middleware access
    _observability_config = config
    
    # Setup tracing
    if config.tracing_enabled:
        setup_tracing(config)
        instrument_fastapi(app)
    
    # Setup logging
    if config.logging_enabled:
        setup_logging(config)
    
    # Initialize redaction filter if enabled
    if config.log_redaction_enabled:
        _redaction_filter = create_redaction_filter(
            additional_keys=config.sensitive_field_keys,
            additional_patterns=config.sensitive_field_patterns,
            mask_value=config.redaction_mask_value,
            mask_length=config.redaction_mask_length,
        )
    
    # Setup metrics
    if config.metrics_enabled:
        metrics = setup_metrics(config)
        
        # Add metrics endpoint
        @app.get(config.metrics_path)
        async def metrics_endpoint():
            from .metrics import get_metrics_response
            content, content_type = get_metrics_response()
            return Response(content=content, media_type=content_type)
    
    # Add observability middleware
    app.add_middleware(ObservabilityMiddleware)
    
    logger.info(
        f"Observability configured for {config.service_name}",
        extra={
            "extra_fields": {
                "service_name": config.service_name,
                "tracing_enabled": config.tracing_enabled,
                "logging_enabled": config.logging_enabled,
                "metrics_enabled": config.metrics_enabled,
                "log_request_body": config.log_request_body,
                "log_response_body": config.log_response_body,
                "log_redaction_enabled": config.log_redaction_enabled,
            }
        },
    )
