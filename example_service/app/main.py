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
