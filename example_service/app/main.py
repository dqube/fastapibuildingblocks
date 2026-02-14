"""FastAPI application main module."""

import os
from contextlib import asynccontextmanager
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
    from fastapi_building_blocks.infrastructure.messaging import (
        KafkaConfig,
        create_event_publisher,
        InboxIntegrationEventConsumer,
        OutboxRelay,
    )
    from .domain.events.message_events import MessageSentIntegrationEvent
    from .application.handlers.message_integration_handlers import MessageSentIntegrationEventHandler
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    print("Warning: Kafka modules not available. Install with kafka extras.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup
    from .core.database import init_db
    await init_db()
    
    # Initialize Kafka producer and consumer
    if KAFKA_AVAILABLE:
        try:
            from .core.database import get_session_factory
            
            # Create Kafka configuration with inbox/outbox patterns
            kafka_config = KafkaConfig(
                bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
                service_name=settings.APP_NAME,
                consumer_group_id=os.getenv("KAFKA_CONSUMER_GROUP", f"{settings.APP_NAME.lower()}-group"),
                enable_outbox=settings.KAFKA_ENABLE_OUTBOX,
                enable_inbox=settings.KAFKA_ENABLE_INBOX,
            )
            
            # Initialize producer (factory chooses outbox or direct based on config)
            # For outbox pattern, we'll create it per-request with database session
            app.state.kafka_config = kafka_config
            
            # Start outbox relay worker if outbox is enabled
            if kafka_config.enable_outbox:
                session_factory = get_session_factory()
                app.state.outbox_relay = OutboxRelay(
                    kafka_config=kafka_config,
                    session_factory=session_factory,
                    polling_interval=5.0,  # Check outbox every 5 seconds
                )
                await app.state.outbox_relay.start()
                print(f"✅ Outbox relay started (polling every 5s)")
            else:
                # For direct publishing, create and start the publisher (no outbox)
                app.state.kafka_producer = create_event_publisher(kafka_config)
                await app.state.kafka_producer.start()
                print(f"✅ Direct Kafka publisher initialized (no outbox)")
            
            # Initialize consumer with inbox pattern support
            session_factory = get_session_factory()
            app.state.kafka_consumer = InboxIntegrationEventConsumer(
                kafka_config=kafka_config,
                session_factory=session_factory,
            )
            
            # Register integration event handler
            app.state.kafka_consumer.register_handler(
                MessageSentIntegrationEvent,
                MessageSentIntegrationEventHandler()
            )
            
            # Start consuming from the topic
            await app.state.kafka_consumer.start(["integration-events.message_sent"])
            
            print(f"✅ Kafka initialized successfully")
            print(f"   - Producer: {kafka_config.bootstrap_servers}")
            print(f"   - Consumer Group: {kafka_config.consumer_group_id}")
            print(f"   - Outbox Pattern: {'✅ Enabled' if kafka_config.enable_outbox else '❌ Disabled'}")
            print(f"   - Inbox Pattern: {'✅ Enabled' if kafka_config.enable_inbox else '❌ Disabled'}")
            print(f"   - Listening to: integration-events.message_sent")
            
        except Exception as e:
            print(f"⚠️ Failed to initialize Kafka: {e}")
            print("   - Message endpoints will not work without Kafka")
            import traceback
            traceback.print_exc()
    
    yield
    
    # Shutdown
    from .core.database import close_db
    await close_db()
    
    # Stop Kafka producer, consumer, and outbox relay
    if KAFKA_AVAILABLE:
        try:
            if hasattr(app.state, 'outbox_relay'):
                await app.state.outbox_relay.stop()
                print("✅ Outbox relay stopped")
            if hasattr(app.state, 'kafka_producer'):
                await app.state.kafka_producer.stop()
            if hasattr(app.state, 'kafka_consumer'):
                await app.state.kafka_consumer.stop()
            print("✅ Kafka stopped successfully")
        except Exception as e:
            print(f"⚠️ Error stopping Kafka: {e}")


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
        lifespan=lifespan,
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
