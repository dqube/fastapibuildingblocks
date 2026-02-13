"""
Distributed tracing with OpenTelemetry and Tempo backend.
"""

import functools
from typing import Optional, Callable, Any
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from .config import ObservabilityConfig


_tracer_provider: Optional[TracerProvider] = None
_config: Optional[ObservabilityConfig] = None


def setup_tracing(config: ObservabilityConfig) -> None:
    """
    Initialize OpenTelemetry tracing with Tempo backend.
    
    Args:
        config: Observability configuration
    """
    global _tracer_provider, _config
    
    if not config.tracing_enabled:
        return
    
    _config = config
    
    # Create resource with service information
    resource = Resource.create({
        SERVICE_NAME: config.service_name,
        SERVICE_VERSION: config.service_version,
        "environment": config.environment,
        "deployment.environment": config.deployment_environment,
        **config.custom_attributes,
    })
    
    # Create tracer provider
    _tracer_provider = TracerProvider(resource=resource)
    
    # Configure OTLP exporter to send traces to Tempo (via OpenTelemetry Collector)
    otlp_exporter = OTLPSpanExporter(
        endpoint=config.tempo_endpoint,
        insecure=config.otlp_insecure,
    )
    
    # Add span processor with batch export
    _tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    # Set as global tracer provider
    trace.set_tracer_provider(_tracer_provider)


def get_tracer(name: str = __name__) -> trace.Tracer:
    """
    Get a tracer instance.
    
    Args:
        name: Tracer name (usually __name__ of the module)
        
    Returns:
        OpenTelemetry Tracer instance
    """
    return trace.get_tracer(name)


def trace_operation(operation_name: Optional[str] = None, attributes: Optional[dict] = None):
    """
    Decorator to trace a function or method execution.
    
    Args:
        operation_name: Custom operation name (defaults to function name)
        attributes: Additional attributes to add to the span
        
    Example:
        @trace_operation("create_user", {"user.type": "admin"})
        async def create_user(user_data):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if _config is None or not _config.tracing_enabled:
                return await func(*args, **kwargs)
            
            tracer = get_tracer(func.__module__)
            span_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with tracer.start_as_current_span(span_name) as span:
                # Add custom attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                # Add function arguments as attributes (limited)
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("result.success", True)
                    return result
                except Exception as e:
                    span.set_attribute("result.success", False)
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if _config is None or not _config.tracing_enabled:
                return func(*args, **kwargs)
            
            tracer = get_tracer(func.__module__)
            span_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with tracer.start_as_current_span(span_name) as span:
                # Add custom attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                # Add function arguments as attributes (limited)
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("result.success", True)
                    return result
                except Exception as e:
                    span.set_attribute("result.success", False)
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


@contextmanager
def trace_context(span_name: str, attributes: Optional[dict] = None):
    """
    Context manager for tracing a code block.
    
    Args:
        span_name: Name of the span
        attributes: Additional attributes
        
    Example:
        with trace_context("database_query", {"query.type": "SELECT"}):
            results = await db.execute(query)
    """
    if _config is None or not _config.tracing_enabled:
        yield
        return
    
    tracer = get_tracer(__name__)
    
    with tracer.start_as_current_span(span_name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        
        try:
            yield span
            span.set_attribute("result.success", True)
        except Exception as e:
            span.set_attribute("result.success", False)
            span.set_attribute("error.type", type(e).__name__)
            span.set_attribute("error.message", str(e))
            span.record_exception(e)
            raise


def instrument_fastapi(app):
    """
    Automatically instrument a FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    if _config is None or not _config.tracing_enabled:
        return
    
    FastAPIInstrumentor.instrument_app(app)
