"""
OpenTelemetry observability building blocks for FastAPI applications.

This package provides:
- Distributed tracing with OpenTelemetry and Tempo
- Structured logging with Loki integration
- Metrics collection with Prometheus
- Automatic instrumentation for mediator pattern
"""

from .config import ObservabilityConfig
from .tracing import setup_tracing, get_tracer, trace_operation
from .logging import setup_logging, get_logger
from .metrics import setup_metrics, get_metrics
from .middleware import ObservabilityMiddleware, setup_observability

__all__ = [
    "ObservabilityConfig",
    "setup_tracing",
    "get_tracer",
    "trace_operation",
    "setup_logging",
    "get_logger",
    "setup_metrics",
    "get_metrics",
    "ObservabilityMiddleware",
    "setup_observability",
]
