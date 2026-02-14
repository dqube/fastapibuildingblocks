"""
Observability configuration for OpenTelemetry, tracing, logging, and metrics.
"""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class ObservabilityConfig:
    """Configuration for observability features."""
    
    # Service identification
    service_name: str = "fastapi-service"
    service_version: str = "1.0.0"
    environment: str = "development"
    
    # Enable/disable features
    tracing_enabled: bool = True
    logging_enabled: bool = True
    metrics_enabled: bool = True
    
    # Log redaction configuration
    log_redaction_enabled: bool = True
    sensitive_field_keys: List[str] = field(default_factory=list)  # Additional keys to redact
    sensitive_field_patterns: List[str] = field(default_factory=list)  # Regex patterns
    redaction_mask_value: str = "***REDACTED***"
    redaction_mask_length: bool = True  # Show length of redacted values
    
    # HTTP request/response logging configuration (similar to .NET middleware)
    log_request_body: bool = False  # Log request body (with redaction)
    log_request_headers: bool = False  # Log request headers (with redaction)
    log_response_body: bool = False  # Log response body (with redaction)
    log_response_headers: bool = False  # Log response headers (with redaction)
    max_body_log_size: int = 10000  # Max size of body to log (bytes)
    exclude_paths: List[str] = field(default_factory=lambda: ["/health", "/metrics"])  # Paths to exclude from detailed logging
    
    # OpenTelemetry Collector endpoint
    otlp_endpoint: str = "http://localhost:4317"
    otlp_insecure: bool = True
    
    # Tempo configuration
    tempo_endpoint: Optional[str] = None  # Uses OTLP endpoint by default
    
    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "json"  # json or text
    
    # Metrics configuration
    metrics_port: int = 9090
    metrics_path: str = "/metrics"
    
    # Sampling configuration
    trace_sample_rate: float = 1.0  # 1.0 = 100% sampling
    
    # Additional attributes
    deployment_environment: Optional[str] = None
    custom_attributes: dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Set defaults after initialization."""
        if self.tempo_endpoint is None:
            self.tempo_endpoint = self.otlp_endpoint
        
        if self.deployment_environment is None:
            self.deployment_environment = self.environment
