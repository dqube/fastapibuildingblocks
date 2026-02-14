#!/usr/bin/env python3
"""
Test script to demonstrate observability features.

This script tests that:
1. Observability modules load correctly
2. Configuration works
3. Tracing, logging, and metrics can be initialized
4. Mediator pattern with observability works
"""

import sys
from io import StringIO


def test_imports():
    """Test that all observability modules can be imported."""
    print("🧪 Testing imports...")
    
    try:
        from building_blocks.observability import (
            ObservabilityConfig,
            setup_tracing,
            get_tracer,
            trace_operation,
            setup_logging,
            get_logger,
            setup_metrics,
            get_metrics,
            ObservabilityMiddleware,
            setup_observability,
        )
        print("   ✅ All observability modules imported successfully")
        return True
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        return False


def test_configuration():
    """Test observability configuration."""
    print("\n🧪 Testing configuration...")
    
    try:
        from building_blocks.observability import ObservabilityConfig
        
        config = ObservabilityConfig(
            service_name="test-service",
            service_version="1.0.0",
            environment="test",
            tracing_enabled=True,
            logging_enabled=True,
            metrics_enabled=True,
        )
        
        assert config.service_name == "test-service"
        assert config.service_version == "1.0.0"
        assert config.tracing_enabled is True
        
        print("   ✅ Configuration works correctly")
        return True
    except Exception as e:
        print(f"   ❌ Configuration error: {e}")
        return False


def test_tracing():
    """Test tracing setup and usage."""
    print("\n🧪 Testing tracing...")
    
    try:
        from building_blocks.observability import (
            ObservabilityConfig,
            setup_tracing,
            get_tracer,
            trace_operation,
        )
        
        config = ObservabilityConfig(
            service_name="test-service",
            tracing_enabled=True,
        )
        
        setup_tracing(config)
        tracer = get_tracer(__name__)
        
        # Test basic span creation
        with tracer.start_as_current_span("test_span") as span:
            span.set_attribute("test", "value")
        
        # Test trace_operation decorator
        @trace_operation("test_function")
        async def test_func():
            return "success"
        
        import asyncio
        result = asyncio.run(test_func())
        assert result == "success"
        
        print("   ✅ Tracing works correctly")
        return True
    except Exception as e:
        print(f"   ❌ Tracing error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_logging():
    """Test logging setup and usage."""
    print("\n🧪 Testing logging...")
    
    try:
        from building_blocks.observability import (
            ObservabilityConfig,
            setup_logging,
            get_logger,
        )
        
        config = ObservabilityConfig(
            service_name="test-service",
            logging_enabled=True,
            log_format="json",
        )
        
        setup_logging(config)
        logger = get_logger(__name__)
        
        # Capture log output
        logger.info("Test log message")
        
        print("   ✅ Logging works correctly")
        return True
    except Exception as e:
        print(f"   ❌ Logging error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metrics():
    """Test metrics setup and usage."""
    print("\n🧪 Testing metrics...")
    
    try:
        from building_blocks.observability import (
            ObservabilityConfig,
            setup_metrics,
            get_metrics,
        )
        
        config = ObservabilityConfig(
            service_name="test-service",
            metrics_enabled=True,
        )
        
        collector = setup_metrics(config)
        assert collector is not None
        
        metrics = get_metrics()
        assert metrics is not None
        
        # Test recording a metric
        metrics.mediator_requests_total.labels(
            request_type="TestCommand",
            handler="TestHandler",
            status="success",
        ).inc()
        
        print("   ✅ Metrics work correctly")
        return True
    except Exception as e:
        print(f"   ❌ Metrics error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mediator_instrumentation():
    """Test that mediator is instrumented with observability."""
    print("\n🧪 Testing mediator instrumentation...")
    
    try:
        from building_blocks.application.mediator import (
            Mediator,
            Request,
            RequestHandler,
        )
        from building_blocks.observability import ObservabilityConfig, setup_tracing
        
        # Setup observability
        config = ObservabilityConfig(service_name="test-service")
        setup_tracing(config)
        
        # Define a test command and handler
        class TestCommand(Request):
            value: str
        
        class TestHandler(RequestHandler[TestCommand, str]):
            async def handle(self, request: TestCommand) -> str:
                return f"Handled: {request.value}"
        
        # Create mediator and register handler
        mediator = Mediator()
        mediator.register_handler(TestCommand, TestHandler())
        
        # Execute command
        import asyncio
        result = asyncio.run(mediator.send(TestCommand(value="test")))
        
        assert result == "Handled: test"
        
        print("   ✅ Mediator instrumentation works correctly")
        return True
    except Exception as e:
        print(f"   ❌ Mediator instrumentation error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fastapi_integration():
    """Test FastAPI integration."""
    print("\n🧪 Testing FastAPI integration...")
    
    try:
        from fastapi import FastAPI
        from building_blocks.observability import (
            setup_observability,
            ObservabilityConfig,
        )
        
        app = FastAPI()
        
        config = ObservabilityConfig(
            service_name="test-api",
            tracing_enabled=True,
            logging_enabled=True,
            metrics_enabled=True,
        )
        
        setup_observability(app, config)
        
        # Check that metrics endpoint was added
        routes = [route.path for route in app.routes]
        assert "/metrics" in routes
        
        print("   ✅ FastAPI integration works correctly")
        return True
    except Exception as e:
        print(f"   ❌ FastAPI integration error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("🔭 Observability Features Test Suite")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_configuration,
        test_tracing,
        test_logging,
        test_metrics,
        test_mediator_instrumentation,
        test_fastapi_integration,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Unexpected error in {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 Test Results")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✨ All tests passed! Observability is fully functional.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
