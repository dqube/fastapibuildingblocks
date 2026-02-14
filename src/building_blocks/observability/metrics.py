"""
Metrics collection with Prometheus.
"""

from typing import Optional, Dict, List
from dataclasses import dataclass, field

from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST

from .config import ObservabilityConfig


_registry: Optional[CollectorRegistry] = None
_config: Optional[ObservabilityConfig] = None
_metrics: Dict[str, any] = {}


@dataclass
class MetricsCollector:
    """Container for application metrics."""
    
    registry: CollectorRegistry = field(default_factory=CollectorRegistry)
    
    # HTTP metrics
    http_requests_total: Optional[Counter] = None
    http_request_duration_seconds: Optional[Histogram] = None
    http_requests_in_progress: Optional[Gauge] = None
    
    # Mediator metrics
    mediator_requests_total: Optional[Counter] = None
    mediator_request_duration_seconds: Optional[Histogram] = None
    mediator_requests_in_progress: Optional[Gauge] = None
    mediator_request_errors_total: Optional[Counter] = None
    
    # Application metrics
    app_info: Optional[Info] = None
    
    def __post_init__(self):
        """Initialize all metrics."""
        # HTTP metrics
        self.http_requests_total = Counter(
            "http_requests_total",
            "Total number of HTTP requests",
            ["method", "endpoint", "status"],
            registry=self.registry,
        )
        
        self.http_request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint"],
            registry=self.registry,
        )
        
        self.http_requests_in_progress = Gauge(
            "http_requests_in_progress",
            "Number of HTTP requests in progress",
            ["method", "endpoint"],
            registry=self.registry,
        )
        
        # Mediator metrics
        self.mediator_requests_total = Counter(
            "mediator_requests_total",
            "Total number of mediator requests",
            ["request_type", "handler", "status"],
            registry=self.registry,
        )
        
        self.mediator_request_duration_seconds = Histogram(
            "mediator_request_duration_seconds",
            "Mediator request duration in seconds",
            ["request_type", "handler"],
            registry=self.registry,
        )
        
        self.mediator_requests_in_progress = Gauge(
            "mediator_requests_in_progress",
            "Number of mediator requests in progress",
            ["request_type"],
            registry=self.registry,
        )
        
        self.mediator_request_errors_total = Counter(
            "mediator_request_errors_total",
            "Total number of mediator request errors",
            ["request_type", "handler", "error_type"],
            registry=self.registry,
        )
        
        # Application info
        self.app_info = Info(
            "app_info",
            "Application information",
            registry=self.registry,
        )


def setup_metrics(config: ObservabilityConfig) -> MetricsCollector:
    """
    Initialize Prometheus metrics.
    
    Args:
        config: Observability configuration
        
    Returns:
        MetricsCollector instance
    """
    global _registry, _config, _metrics
    
    if not config.metrics_enabled:
        return None
    
    _config = config
    
    # Create metrics collector
    collector = MetricsCollector()
    _registry = collector.registry
    
    # Set application info
    collector.app_info.info({
        "service_name": config.service_name,
        "version": config.service_version,
        "environment": config.environment,
    })
    
    _metrics["collector"] = collector
    
    return collector


def get_metrics() -> Optional[MetricsCollector]:
    """
    Get the metrics collector instance.
    
    Returns:
        MetricsCollector instance or None if metrics not enabled
    """
    return _metrics.get("collector")


def get_metrics_response() -> tuple:
    """
    Generate Prometheus metrics response.
    
    Returns:
        Tuple of (content, content_type) for use in HTTP response
    """
    if _registry is None:
        return b"", "text/plain"
    
    content = generate_latest(_registry)
    return content, CONTENT_TYPE_LATEST


def record_mediator_request(
    request_type: str,
    handler: str,
    duration: float,
    success: bool,
    error_type: Optional[str] = None,
):
    """
    Record metrics for a mediator request.
    
    Args:
        request_type: Type of request (command/query class name)
        handler: Handler class name
        duration: Request duration in seconds
        success: Whether the request succeeded
        error_type: Type of error if failed
    """
    collector = get_metrics()
    if collector is None:
        return
    
    status = "success" if success else "error"
    
    # Record total requests
    collector.mediator_requests_total.labels(
        request_type=request_type,
        handler=handler,
        status=status,
    ).inc()
    
    # Record duration
    collector.mediator_request_duration_seconds.labels(
        request_type=request_type,
        handler=handler,
    ).observe(duration)
    
    # Record errors
    if not success and error_type:
        collector.mediator_request_errors_total.labels(
            request_type=request_type,
            handler=handler,
            error_type=error_type,
        ).inc()
