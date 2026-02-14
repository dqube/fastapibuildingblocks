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

# Import Kafka (optional - gracefully handle if not installed)
try:
    from fastapi_building_blocks.infrastructure.messaging.kafka_config import KafkaConfig
    from fastapi_building_blocks.infrastructure.messaging.kafka_producer import KafkaIntegrationEventPublisher
    from fastapi_building_blocks.infrastructure.messaging.kafka_consumer import KafkaIntegrationEventConsumer
    from .domain.events.message_events import MessageSentIntegrationEvent
    from .application.handlers.message_integration_handlers import MessageSentIntegrationEventHandler
    from .api.dependencies import set_kafka_publisher
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    print("Warning: Kafka modules not available. Install with kafka extras.")



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
        """Initialize database connection and Kafka on startup."""
        from .core.database import init_db
        await init_db()
        
        # Initialize Kafka producer and consumer
        if KAFKA_AVAILABLE:
            try:
                # Create Kafka configuration from environment
                kafka_config = KafkaConfig(
                    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
                    service_name=settings.APP_NAME,
                    consumer_group_id=os.getenv("KAFKA_CONSUMER_GROUP", f"{settings.APP_NAME.lower()}-group"),
                )
                
                # Initialize producer
                app.state.kafka_producer = KafkaIntegrationEventPublisher(kafka_config)
                await app.state.kafka_producer.start()
                
                # Set global publisher for dependency injection
                set_kafka_publisher(app.state.kafka_producer)
                
                # Initialize consumer
                app.state.kafka_consumer = KafkaIntegrationEventConsumer(kafka_config)
                
                # Register integration event handler
                # The handler will create its own database session for processing
                app.state.kafka_consumer.register_handler(
                    MessageSentIntegrationEvent,
                    MessageSentIntegrationEventHandler()
                )
                
                # Start consuming from the topic
                await app.state.kafka_consumer.start(["integration-events.message_sent"])
                
                print(f"✅ Kafka initialized successfully")
                print(f"   - Producer: {kafka_config.bootstrap_servers}")
                print(f"   - Consumer Group: {kafka_config.consumer_group_id}")
                print(f"   - Listening to: integration-events.message_sent")
                
            except Exception as e:
                print(f"⚠️ Failed to initialize Kafka: {e}")
                print("   - Message endpoints will not work without Kafka")
    
    @app.on_event("shutdown")
    async def shutdown():
        """Close database connection and Kafka on shutdown."""
        from .core.database import close_db
        await close_db()
        
        # Stop Kafka producer and consumer
        if KAFKA_AVAILABLE and hasattr(app.state, 'kafka_producer'):
            try:
                await app.state.kafka_producer.stop()
                await app.state.kafka_consumer.stop()
                print("✅ Kafka stopped successfully")
            except Exception as e:
                print(f"⚠️ Error stopping Kafka: {e}")
    
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
