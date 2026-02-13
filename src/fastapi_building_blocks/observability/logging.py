"""Structured logging with Loki integration."""

import logging
import sys
import json
from datetime import datetime
from typing import Optional, Dict, Any

from opentelemetry import trace
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk.resources import Resource

from .config import ObservabilityConfig
from .redaction import RedactionFilter, create_redaction_filter


_config: Optional[ObservabilityConfig] = None
_logger_initialized: bool = False
_redaction_filter: Optional[RedactionFilter] = None
_logger_provider: Optional[LoggerProvider] = None


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging compatible with Loki."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Get current span context for trace correlation
        span = trace.get_current_span()
        span_context = span.get_span_context()
        
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add trace context for correlation
        if span_context.is_valid:
            log_data["trace_id"] = format(span_context.trace_id, "032x")
            log_data["span_id"] = format(span_context.span_id, "016x")
            log_data["trace_flags"] = format(span_context.trace_flags, "02x")
        
        # Add service information if available
        if _config:
            log_data["service"] = _config.service_name
            log_data["environment"] = _config.environment
        
        # Add exception information
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add custom fields from extra
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        # Apply redaction if enabled
        if _redaction_filter:
            log_data = _redaction_filter.redact_dict(log_data)
        
        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter with trace context."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as text with trace context."""
        # Get current span context
        span = trace.get_current_span()
        span_context = span.get_span_context()
        
        # Apply redaction to message if enabled
        if _redaction_filter and isinstance(record.msg, str):
            record.msg = _redaction_filter.redact_string(record.msg)
        
        # Base format
        base_format = f"%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        # Add trace context if available
        if span_context.is_valid:
            trace_id = format(span_context.trace_id, "032x")
            span_id = format(span_context.span_id, "016x")
            base_format = f"{base_format} [trace_id={trace_id} span_id={span_id}]"
        
        formatter = logging.Formatter(base_format)
        return formatter.format(record)


def setup_logging(config: ObservabilityConfig) -> None:
    """
    Configure structured logging.
    
    Args:
        config: Observability configuration
    """
    global _config, _logger_initialized, _redaction_filter, _logger_provider
    
    if not config.logging_enabled or _logger_initialized:
        return
    
    _config = config
    
    # Initialize redaction filter if enabled
    if config.log_redaction_enabled:
        _redaction_filter = create_redaction_filter(
            additional_keys=config.sensitive_field_keys,
            additional_patterns=config.sensitive_field_patterns,
            mask_value=config.redaction_mask_value,
            mask_length=config.redaction_mask_length,
        )
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(config.log_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Create console handler for stdout logging
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(config.log_level)
    
    # Set formatter based on configuration
    if config.log_format == "json":
        formatter = JsonFormatter()
    else:
        formatter = TextFormatter()
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Setup OpenTelemetry LoggerProvider for sending logs to OTLP
    try:
        # Create resource with service information
        resource = Resource.create({
            "service.name": config.service_name,
            "service.version": config.service_version,
            "service.environment": config.environment,
        })
        
        # Create LoggerProvider
        _logger_provider = LoggerProvider(resource=resource)
        
        # Create OTLP Log Exporter
        otlp_log_exporter = OTLPLogExporter(
            endpoint=config.otlp_endpoint,
            insecure=config.otlp_insecure,
        )
        
        # Add BatchLogRecordProcessor
        _logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(otlp_log_exporter)
        )
        
        # Create and add OTEL logging handler
        otel_handler = LoggingHandler(
            level=logging.NOTSET,
            logger_provider=_logger_provider,
        )
        
        # Add OTEL handler to root logger
        root_logger.addHandler(otel_handler)
        
    except Exception as e:
        # If OTLP setup fails, log warning but continue with console logging
        print(f"Warning: Failed to setup OTLP log export: {e}", file=sys.stderr)
    
    _logger_initialized = True


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (usually __name__ of the module)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that adds extra fields to all log records."""
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Process log message and add extra fields."""
        # Ensure extra exists
        if "extra" not in kwargs:
            kwargs["extra"] = {}
        
        # Add custom fields
        if self.extra:
            kwargs["extra"]["extra_fields"] = self.extra
        
        return msg, kwargs


def get_logger_with_context(name: str = __name__, **context) -> LoggerAdapter:
    """
    Get a logger with additional context fields.
    
    Args:
        name: Logger name
        **context: Additional context fields to include in all log records
        
    Returns:
        LoggerAdapter instance with context
        
    Example:
        logger = get_logger_with_context(__name__, user_id="123", action="create")
        logger.info("User action performed")
    """
    logger = get_logger(name)
    return LoggerAdapter(logger, context)
