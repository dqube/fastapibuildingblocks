"""
FastAPI middleware for automatic observability instrumentation.
"""

import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from .config import ObservabilityConfig
from .tracing import setup_tracing, instrument_fastapi, get_tracer
from .logging import setup_logging, get_logger
from .metrics import setup_metrics, get_metrics


logger = get_logger(__name__)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically instrument HTTP requests with observability."""
    
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
        
        # Extract request details
        method = request.method
        path = request.url.path
        
        # Track in-progress requests
        if metrics:
            metrics.http_requests_in_progress.labels(method=method, endpoint=path).inc()
        
        # Record start time
        start_time = time.time()
        
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
            
            # Log request
            logger.info(
                f"{method} {path} - {response.status_code}",
                extra={
                    "extra_fields": {
                        "http.method": method,
                        "http.path": path,
                        "http.status_code": response.status_code,
                        "http.duration_seconds": duration,
                    }
                },
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
            
            # Log error
            logger.error(
                f"{method} {path} - ERROR: {str(e)}",
                exc_info=True,
                extra={
                    "extra_fields": {
                        "http.method": method,
                        "http.path": path,
                        "http.error_type": type(e).__name__,
                        "http.duration_seconds": duration,
                    }
                },
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
    
    Args:
        app: FastAPI application instance
        config: Observability configuration
        
    Example:
        from fastapi import FastAPI
        from fastapi_building_blocks.observability import setup_observability, ObservabilityConfig
        
        app = FastAPI()
        config = ObservabilityConfig(service_name="my-service")
        setup_observability(app, config)
    """
    # Setup tracing
    if config.tracing_enabled:
        setup_tracing(config)
        instrument_fastapi(app)
    
    # Setup logging
    if config.logging_enabled:
        setup_logging(config)
    
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
            }
        },
    )
