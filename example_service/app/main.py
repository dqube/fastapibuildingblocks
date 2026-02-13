"""FastAPI application main module."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import settings
from .api.v1.api import api_router

# Import observability (optional - gracefully handle if not installed)
try:
    from fastapi_building_blocks.observability import (
        setup_observability,
        ObservabilityConfig,
    )
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False
    print("Warning: Observability modules not available. Install with observability extras.")



def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="A FastAPI microservice demonstrating Domain-Driven Design architecture",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    
    # Setup observability (tracing, logging, metrics)
    if OBSERVABILITY_AVAILABLE:
        # Parse sensitive field keys from environment
        sensitive_keys = os.getenv("SENSITIVE_FIELD_KEYS", "").split(",")
        sensitive_keys = [key.strip() for key in sensitive_keys if key.strip()]
        
        observability_config = ObservabilityConfig(
            service_name=settings.APP_NAME,
            service_version=settings.APP_VERSION,
            environment=os.getenv("ENVIRONMENT", "development"),
            # OpenTelemetry Collector endpoint
            otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
            otlp_insecure=True,
            # Enable all features
            tracing_enabled=os.getenv("TRACING_ENABLED", "true").lower() == "true",
            logging_enabled=os.getenv("LOGGING_ENABLED", "true").lower() == "true",
            metrics_enabled=os.getenv("METRICS_ENABLED", "true").lower() == "true",
            # Logging configuration
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_format=os.getenv("LOG_FORMAT", "json"),
            # Metrics configuration
            metrics_port=int(os.getenv("METRICS_PORT", "9090")),
            # Request/Response logging with redaction (.NET-style middleware)
            log_request_body=os.getenv("LOG_REQUEST_BODY", "true").lower() == "true",
            log_request_headers=os.getenv("LOG_REQUEST_HEADERS", "false").lower() == "true",
            log_response_body=os.getenv("LOG_RESPONSE_BODY", "true").lower() == "true",
            log_response_headers=os.getenv("LOG_RESPONSE_HEADERS", "false").lower() == "true",
            # Redaction (protect sensitive data in logs)
            log_redaction_enabled=os.getenv("LOG_REDACTION_ENABLED", "true").lower() == "true",
            sensitive_field_keys=sensitive_keys,
            max_body_log_size=int(os.getenv("MAX_BODY_LOG_SIZE", "10000")),
            exclude_paths=["/health", "/metrics", "/docs", "/redoc", "/openapi.json"],
        )
        setup_observability(app, observability_config)
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API router
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    
    # Database lifecycle events
    @app.on_event("startup")
    async def startup():
        """Initialize database connection on startup."""
        from .core.database import init_db
        await init_db()
    
    @app.on_event("shutdown")
    async def shutdown():
        """Close database connection on shutdown."""
        from .core.database import close_db
        await close_db()
    
    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        """Health check endpoint."""
        return JSONResponse(
            content={
                "status": "healthy",
                "service": settings.APP_NAME,
                "version": settings.APP_VERSION,
            }
        )
    
    # Root endpoint
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint with API information."""
        return JSONResponse(
            content={
                "service": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "docs": "/docs",
                "health": "/health",
            }
        )
    
    return app


# Create application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
