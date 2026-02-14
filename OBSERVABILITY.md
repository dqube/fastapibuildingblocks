# Observability with OpenTelemetry, Tempo, Loki, and Prometheus

## Overview

This FastAPI Building Blocks library includes comprehensive observability features using the modern Grafana stack:

- **OpenTelemetry** - Industry-standard instrumentation
- **Grafana Tempo** - Distributed tracing backend (alternative to Jaeger)
- **Grafana Loki** - Log aggregation system
- **Promtail** - Log collector for Loki
- **Prometheus** - Metrics storage and querying
- **Grafana** - Unified visualization dashboard

## Architecture

```
┌─────────────────┐
│  FastAPI App    │
│  (Your Service) │
└────────┬────────┘
         │
         │ OTLP (gRPC/HTTP)
         ▼
┌─────────────────────┐
│ OpenTelemetry       │
│ Collector           │
└──┬──────┬──────┬───┘
   │      │      │
   │      │      └──────────────┐
   │      │                     │
   ▼      ▼                     ▼
┌─────┐ ┌──────────┐    ┌─────────┐
│Tempo│ │Prometheus│    │  Loki   │
└──┬──┘ └────┬─────┘    └────┬────┘
   │         │               │
   │         │               │
   └─────────┴───────────────┘
                 │
                 ▼
         ┌──────────────┐
         │   Grafana    │
         │ (Port 3000)  │
         └──────────────┘
```

## Features

### 1. Distributed Tracing
- Automatic trace creation for all HTTP requests
- Automatic trace instrumentation for mediator.send() calls
- Trace context propagation across service boundaries
- Correlation between traces, logs, and metrics

### 2. Structured Logging
- JSON-formatted logs for machine parsing
- Automatic trace ID injection into logs
- Log correlation with traces in Grafana
- Support for custom log fields

### 3. Metrics Collection
- HTTP request metrics (rate, duration, status codes)
- Mediator pattern metrics (command/query performance)
- Custom application metrics
- Prometheus-compatible exposition format

### 4. Automatic Instrumentation
The mediator pattern is automatically instrumented to capture:
- Request type (command/query name)
- Handler type
- Execution duration
- Success/failure status
- Error types
- Trace spans for distributed tracing

## Quick Start

### 1. Install Dependencies

```bash
make install
```

### 2. Start Observability Stack

```bash
make obs-up
```

This starts:
- OpenTelemetry Collector (ports 4317, 4318)
- Tempo (port 3200)
- Loki (port 3100)
- Promtail
- Prometheus (port 9090)
- Grafana (port 3000)

### 3. Run Your Application with Observability

```bash
make run-with-obs
```

Or start both at once:

```bash
make obs-all
```

### 4. Access Grafana Dashboard

Open http://localhost:3000 in your browser (anonymous access is enabled).

Navigate to:
- **Dashboards** → **FastAPI** → **FastAPI Observability Dashboard**

## Using Observability in Your Application

### Basic Setup

```python
from fastapi import FastAPI
from building_blocks.observability import setup_observability, ObservabilityConfig

app = FastAPI(title="My Service")

# Configure observability
config = ObservabilityConfig(
    service_name="my-service",
    service_version="1.0.0",
    environment="production",
    otlp_endpoint="http://localhost:4317",
    tracing_enabled=True,
    logging_enabled=True,
    metrics_enabled=True,
    log_format="json",
)

# Setup all observability features
setup_observability(app, config)
```

### Custom Tracing

```python
from building_blocks.observability import trace_operation, trace_context

# Decorator-based tracing
@trace_operation("create_user", {"operation.type": "write"})
async def create_user(user_data):
    # Your code here
    return user

# Context manager tracing
async def process_data():
    with trace_context("database_query", {"query.type": "SELECT"}):
        results = await db.execute(query)
    return results
```

### Custom Logging

```python
from building_blocks.observability import get_logger, get_logger_with_context

# Basic logger
logger = get_logger(__name__)
logger.info("User created successfully")

# Logger with context
logger = get_logger_with_context(__name__, user_id="123", action="create")
logger.info("Processing user action")  # Automatically includes user_id and action
```

### Custom Metrics

```python
from building_blocks.observability import get_metrics

metrics = get_metrics()

# Increment counter
metrics.mediator_requests_total.labels(
    request_type="CreateUser",
    handler="CreateUserHandler",
    status="success"
).inc()

# Record duration
metrics.mediator_request_duration_seconds.labels(
    request_type="CreateUser",
    handler="CreateUserHandler"
).observe(0.123)
```

## Environment Variables

Configure observability behavior with environment variables:

```bash
# OpenTelemetry
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# Feature toggles
TRACING_ENABLED=true
LOGGING_ENABLED=true
METRICS_ENABLED=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json  # or "text"

# Metrics
METRICS_PORT=9090
METRICS_PATH=/metrics

# Service identification
ENVIRONMENT=production
```

## Grafana Dashboard

The pre-configured dashboard includes:

### HTTP Metrics
- **Request Rate** - Requests per second by endpoint
- **Request Duration** - p50, p95, p99 latency
- **Status Codes** - 2xx, 4xx, 5xx distribution

### Mediator Metrics
- **Command/Query Rate** - CQRS pattern metrics
- **Handler Performance** - Duration by handler type
- **Error Rates** - Failed commands/queries

### Logs
- **Structured Logs** - Filterable by level, service, trace ID
- **Trace Correlation** - Click trace ID to view full trace

### Traces
- **Service Map** - Visual service dependencies
- **Trace Timeline** - Detailed span visualization
- **Performance Analysis** - Slow operation detection

## Trace Correlation

All telemetry data is correlated by trace ID:

1. **Logs → Traces**: Click trace ID in logs to view the trace
2. **Traces → Logs**: View logs for a specific trace span
3. **Metrics → Traces**: Exemplars link metrics to traces

## Example Workflow

### 1. Find Slow Requests

In Grafana:
1. Go to **Tempo** datasource
2. Search for traces with duration > 1s
3. Identify slow operations

### 2. View Related Logs

1. Click on a trace span
2. See "View Logs" button
3. See all logs for that trace

### 3. Check Metrics

1. View request rate and duration
2. Identify patterns (spikes, errors)
3. Click exemplar to see sample trace

## Commands Reference

```bash
# Start observability stack
make obs-up

# Stop observability stack
make obs-down

# Restart observability stack
make obs-restart

# View logs from all services
make obs-logs

# Check status
make obs-status

# Clean all data (removes volumes)
make obs-clean

# Run application with observability
make run-with-obs

# Start everything (stack + app)
make obs-all
```

## Accessing Services

| Service                | URL                     | Purpose                    |
|------------------------|-------------------------|----------------------------|
| Grafana                | http://localhost:3000   | Dashboards & visualization |
| Prometheus             | http://localhost:9090   | Metrics queries            |
| Tempo                  | http://localhost:3200   | Trace queries              |
| Loki                   | http://localhost:3100   | Log queries                |
| OTLP Collector (gRPC)  | http://localhost:4317   | Telemetry ingestion        |
| OTLP Collector (HTTP)  | http://localhost:4318   | Telemetry ingestion        |
| Application Metrics    | http://localhost:8000/metrics | App metrics endpoint |

## Automatic Mediator Instrumentation

Every `mediator.send()` call is automatically instrumented:

```python
# This automatically creates:
# - A trace span named "mediator.send.CreateUserCommand"
# - Structured logs with trace correlation
# - Metrics for duration and success/failure
result = await mediator.send(CreateUserCommand(email="user@example.com"))
```

Captured data:
- **Span attributes**: request type, handler type, module
- **Logs**: Start, completion, or error with duration
- **Metrics**: Total requests, duration histogram, error count

## Production Considerations

### Sampling

For high-traffic services, configure sampling:

```python
config = ObservabilityConfig(
    trace_sample_rate=0.1,  # Sample 10% of traces
)
```

### Resource Limits

The default configuration is suitable for development. For production:
1. Increase retention periods (Tempo, Loki)
2. Add persistent volumes
3. Configure resource limits
4. Set up authentication

### Performance Impact

- **Tracing**: Minimal (<1ms per request)
- **Logging**: Low (async writes)
- **Metrics**: Negligible (in-memory counters)

## Troubleshooting

### Application Not Sending Traces

1. Check OTLP endpoint: `echo $OTEL_EXPORTER_OTLP_ENDPOINT`
2. Verify collector is running: `make obs-status`
3. Check collector logs: `docker logs otel-collector`

### No Data in Grafana

1. Wait 1-2 minutes for data propagation
2. Check datasource configuration in Grafana
3. Verify time range in dashboard

### High Memory Usage

1. Reduce retention periods in configs
2. Decrease trace sample rate
3. Limit log volume with filters

## Why Tempo Instead of Jaeger?

**Tempo Advantages:**
- Cloud-native, efficient object storage
- No database required (uses local filesystem or S3)
- Better integration with Grafana stack
- Lower operational overhead
- Built-in trace correlation with logs/metrics

Both are excellent choices. Tempo is preferred for new deployments, especially with the Grafana ecosystem.

## Additional Resources

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Grafana Tempo Documentation](https://grafana.com/docs/tempo/latest/)
- [Grafana Loki Documentation](https://grafana.com/docs/loki/latest/)
- [Prometheus Documentation](https://prometheus.io/docs/)

## Support

For issues or questions:
1. Check logs: `make obs-logs`
2. Verify configuration files in `observability/` directory
3. Review this documentation
