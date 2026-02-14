# Examples & Integration Tests

This directory contains demonstration scripts, example implementations, and integration tests for the FastAPI Building Blocks library.

## Directory Contents

### Demo Scripts (`demo_*.py`)

Standalone demonstration scripts showing how to use various features:

- **demo_exception_handler.py** - Global exception handler with Problem Details
- **demo_http_client.py** - HTTP client wrapper usage examples
- **demo_middleware.py** - Middleware logging demonstrations
- **demo_redaction.py** - Sensitive data redaction in logs
- **demo_redis_api.py** - Redis API usage examples
- **demo_redis_cache.py** - Redis caching demonstrations

### Example Implementations (`example_*.py`)

Complete example implementations of patterns:

- **example_config_with_redis.py** - Redis configuration examples
- **example_configurable_inbox_outbox.py** - Configurable Inbox/Outbox pattern
- **example_kafka_integration.py** - Kafka integration examples
- **example_redaction.py** - Data redaction examples

### Integration Tests (`test_*.py`)

Integration tests that verify end-to-end functionality:

- **test_inbox_outbox_demo.py** - Inbox/Outbox pattern integration test
- **test_inbox_outbox_simple.py** - Simple Inbox/Outbox test
- **test_kafka_simple.py** - Kafka integration test
- **test_mediator.py** - Mediator pattern test
- **test_mediator_e2e.py** - Mediator end-to-end test
- **test_middleware_logging.py** - Middleware logging test
- **test_observability.py** - Observability features test
- **test_redis_api.py** - Redis API integration test
- **test_redis_lua.py** - Redis Lua scripts test

## Running Examples

### Demo Scripts

Run demo scripts directly with Python:

```bash
# From project root
source .venv/bin/activate

# Run a demo
python examples/demo_http_client.py
python examples/demo_redis_cache.py
python examples/demo_exception_handler.py
```

### Integration Tests

Run integration tests with pytest:

```bash
# Run all integration tests
pytest examples/

# Run specific test file
pytest examples/test_mediator_e2e.py

# Run with verbose output
pytest examples/test_kafka_simple.py -v
```

Or run directly with Python:

```bash
python examples/test_redis_lua.py
python examples/test_mediator.py
```

## Requirements

Most examples require:
- Active virtual environment (`.venv`)
- Dependencies installed (`pip install -e .`)
- Running services (for some tests):
  - PostgreSQL (for Inbox/Outbox examples)
  - Redis (for Redis examples)
  - Kafka (for Kafka examples)

## Related Documentation

- **Unit Tests**: See `/tests/` directory for unit tests
- **Documentation**: See `/docs/` directory for detailed documentation
- **Example Service**: See `/example_service/` for a complete reference implementation

## Note

These are **integration tests and demonstrations**, not unit tests. Unit tests are located in the `/tests/` directory and follow a different structure for isolated component testing.
