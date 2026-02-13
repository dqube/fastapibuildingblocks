# Makefile for FastAPI Building Blocks
# Similar to dotnet run/build commands

.PHONY: help install dev run test clean build lint format docker-build docker-deploy obs-up obs-down obs-restart obs-logs kafka-up kafka-down kafka-restart kafka-logs

# Default target
help:
	@echo "FastAPI Building Blocks - Available Commands"
	@echo "=============================================="
	@echo ""
	@echo "Local Development:"
	@echo "  make install      - Install package and dependencies (like: dotnet restore)"
	@echo "  make dev          - Install package in development mode"
	@echo "  make run          - Run the example service (like: dotnet run)"
	@echo "  make restart      - Kill existing process and restart"
	@echo "  make stop         - Stop the running service"
	@echo "  make build        - Build the package (like: dotnet build)"
	@echo "  make test         - Run tests (like: dotnet test)"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build - Build Docker image for example service"
	@echo "  make docker-deploy- Deploy and run in Docker container"
	@echo ""
	@echo "Kafka Stack:"
	@echo "  make kafka-up     - Start Kafka stack (Kafka, Zookeeper, UI, Schema Registry)"
	@echo "  make kafka-down   - Stop Kafka stack"
	@echo "  make kafka-restart- Restart Kafka stack"
	@echo "  make kafka-logs   - View Kafka stack logs"
	@echo "  make kafka-status - Check status of Kafka services"
	@echo "  make kafka-ui     - Open Kafka UI in browser"
	@echo "  make kafka-clean  - Stop Kafka and remove volumes"
	@echo ""
	@echo "Observability Stack:"
	@echo "  make obs-up       - Start observability stack (Tempo, Loki, Prometheus, Grafana)"
	@echo "  make obs-down     - Stop observability stack"
	@echo "  make obs-restart  - Restart observability stack"
	@echo "  make obs-logs     - View observability stack logs"
	@echo "  make obs-status   - Check status of observability services"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint         - Run code linters"
	@echo "  make format       - Format code with black"
	@echo "  make clean        - Clean build artifacts"
	@echo ""

# Install package and dependencies
install:
	@echo "📦 Installing fastapi-building-blocks..."
	python3 -m pip install -e .
	@echo "✅ Installation complete!"

# Install in development mode with dev dependencies
dev:
	@echo "📦 Installing in development mode..."
	python3 -m pip install -e ".[dev]"
	@echo "✅ Development environment ready!"

# Run the example service (equivalent to dotnet run)
run:
	@echo "🚀 Starting User Management Service..."
	@echo ""
	@cd example_service && python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Stop the running service
stop:
	@echo "🛑 Stopping service..."
	@lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "No process running on port 8000"
	@echo "✅ Service stopped!"

# Restart the service (kill and run)
restart: stop
	@echo "🔄 Restarting service..."
	@sleep 1
	@cd example_service && python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run with production settings
run-prod:
	@echo "🚀 Starting User Management Service (Production)..."
	@cd example_service && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Build the package (equivalent to dotnet build)
build:
	@echo "🔨 Building package..."
	python3 -m build
	@echo "✅ Build complete! Artifacts in dist/"

# Run tests (equivalent to dotnet test)
test:
	@echo "🧪 Running tests..."
	pytest tests/ -v --cov=src/fastapi_building_blocks --cov-report=term-missing

# Run example service tests
test-example:
	@echo "🧪 Running example service tests..."
	@cd example_service && pytest tests/ -v

# Run all tests
test-all: test test-example
	@echo "✅ All tests passed!"

# Lint code
lint:
	@echo "🔍 Linting code..."
	ruff check src/ tests/
	mypy src/

# Format code
format:
	@echo "✨ Formatting code..."
	black src/ tests/ example_service/
	ruff check --fix src/ tests/

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf src/*.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "✅ Clean complete!"

# Quick check before commit
check: format lint test
	@echo "✅ All checks passed!"

# Watch for changes and auto-reload (development)
watch:
	@echo "👀 Watching for changes..."
	@cd example_service && watchmedo auto-restart --directory=. --pattern=*.py --recursive -- python3 -m uvicorn app.main:app --reload

# Show API documentation
docs:
	@echo "📚 Opening API documentation..."
	@echo "   Swagger UI: http://localhost:8000/docs"
	@echo "   ReDoc: http://localhost:8000/redoc"
	@open http://localhost:8000/docs 2>/dev/null || xdg-open http://localhost:8000/docs 2>/dev/null || echo "Please open http://localhost:8000/docs in your browser"

# Docker commands (delegates to example_service)
docker-build:
	@echo "🐳 Building Docker image from root..."
	docker build -t user-management-service:latest -f Dockerfile .
	@echo "✅ Docker image built successfully!"

docker-run:
	@echo "🐳 Running application in Docker..."
	@echo ""
	@echo "Service will be available at:"
	@echo "  - API: http://localhost:8000"
	@echo "  - Docs: http://localhost:8000/docs"
	@echo "  - ReDoc: http://localhost:8000/redoc"
	@echo ""
	docker run -d --name user-management-api -p 8000:8000 user-management-service:latest
	@echo "✅ Container started!"
	@echo "Use 'make docker-logs' to view logs"

docker-deploy: docker-stop docker-build docker-run
	@echo "✅ Deployment complete!"
	@sleep 3
	@echo ""
	@echo "Testing endpoint..."
	@curl -s http://localhost:8000/api/v1/users/ | head -20 || echo "Service starting up..."

docker-stop:
	@echo "🛑 Stopping Docker container..."
	@docker stop user-management-api 2>/dev/null || echo "Container not running"
	@docker rm user-management-api 2>/dev/null || echo "Container already removed"
	@echo "✅ Container stopped and removed!"

docker-logs:
	@echo "📋 Container logs:"
	@echo "=================="
	docker logs -f user-management-api

# Observability stack commands
obs-up:
	@echo "🔭 Starting Observability Stack..."
	@echo ""
	@echo "Starting services:"
	@echo "  - OpenTelemetry Collector (ports: 4317, 4318)"
	@echo "  - Tempo (port: 3200)"
	@echo "  - Loki (port: 3100)"
	@echo "  - Promtail"
	@echo "  - Prometheus (port: 9090)"
	@echo "  - Grafana (port: 3000)"
	@echo ""
	docker-compose -f docker-compose.observability.yml up -d
	@echo ""
	@echo "✅ Observability stack started!"
	@echo ""
	@echo "Access points:"
	@echo "  - Grafana: http://localhost:3000 (anonymous access enabled)"
	@echo "  - Prometheus: http://localhost:9090"
	@echo "  - Tempo: http://localhost:3200"
	@echo "  - Loki: http://localhost:3100"
	@echo ""
	@echo "💡 Tip: Run your application with OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317"

obs-down:
	@echo "🛑 Stopping Observability Stack..."
	docker-compose -f docker-compose.observability.yml down
	@echo "✅ Observability stack stopped!"

obs-restart: obs-down obs-up
	@echo "✅ Observability stack restarted!"

obs-logs:
	@echo "📋 Observability stack logs:"
	@echo "============================"
	docker-compose -f docker-compose.observability.yml logs -f

obs-status:
	@echo "📊 Observability Stack Status:"
	@echo "=============================="
	@docker-compose -f docker-compose.observability.yml ps

obs-clean:
	@echo "🧹 Cleaning observability data..."
	docker-compose -f docker-compose.observability.yml down -v
	@echo "✅ Observability volumes removed!"

# Run with observability enabled
run-with-obs:
	@echo "🚀 Starting service with observability..."
	@echo ""
	@echo "Checking observability stack..."
	@docker-compose -f docker-compose.observability.yml ps | grep -q "Up" || (echo "❌ Observability stack not running. Start it with 'make obs-up'" && exit 1)
	@echo "✅ Observability stack is running"
	@echo ""
	@echo "Starting service..."
	@cd example_service && \
		OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 \
		TRACING_ENABLED=true \
		LOGGING_ENABLED=true \
		METRICS_ENABLED=true \
		LOG_FORMAT=json \
		LOG_LEVEL=INFO \
		python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Complete observability setup (stack + application)
obs-all: obs-up
	@echo ""
	@echo "⏳ Waiting for stack to initialize (30 seconds)..."
	@sleep 30
	@echo ""
	@echo "🚀 Starting application with observability..."
	@$(MAKE) run-with-obs
# Kafka stack commands
kafka-up:
	@echo "📨 Starting Kafka Stack..."
	@echo ""
	@echo "Starting services:"
	@echo "  - Zookeeper (port: 2181)"
	@echo "  - Kafka Broker (port: 9092)"
	@echo "  - Kafka UI (port: 8080)"
	@echo "  - Schema Registry (port: 8081)"
	@echo ""
	docker-compose -f docker-compose.kafka.yml up -d
	@echo ""
	@echo "✅ Kafka stack started!"
	@echo ""
	@echo "Access points:"
	@echo "  - Kafka UI: http://localhost:8080"
	@echo "  - Kafka Broker: localhost:9092"
	@echo "  - Schema Registry: http://localhost:8081"
	@echo ""
	@echo "💡 Tip: Use KAFKA_BOOTSTRAP_SERVERS=localhost:9092 in your application"

kafka-down:
	@echo "🛑 Stopping Kafka Stack..."
	docker-compose -f docker-compose.kafka.yml down
	@echo "✅ Kafka stack stopped!"

kafka-restart: kafka-down kafka-up
	@echo "✅ Kafka stack restarted!"

kafka-logs:
	@echo "📋 Kafka stack logs:"
	@echo "===================="
	docker-compose -f docker-compose.kafka.yml logs -f

kafka-status:
	@echo "📊 Kafka Stack Status:"
	@echo "======================"
	@docker-compose -f docker-compose.kafka.yml ps

kafka-clean:
	@echo "🧹 Cleaning Kafka data..."
	docker-compose -f docker-compose.kafka.yml down -v
	@echo "✅ Kafka volumes removed!"

kafka-ui:
	@echo "🌐 Opening Kafka UI..."
	@open http://localhost:8080 2>/dev/null || xdg-open http://localhost:8080 2>/dev/null || echo "Please open http://localhost:8080 in your browser"

# Install messaging dependencies (Kafka packages)
install-messaging:
	@echo "📦 Installing messaging dependencies (Kafka)..."
	python3 -m pip install -e ".[messaging]"
	@echo "✅ Messaging dependencies installed!"
	@echo ""
	@echo "Installed packages:"
	@python3 -m pip list | grep -E "(aiokafka|pydantic-settings)"

# Run with Kafka enabled
run-with-kafka:
	@echo "🚀 Starting service with Kafka integration..."
	@echo ""
	@echo "Checking Kafka stack..."
	@docker-compose -f docker-compose.kafka.yml ps | grep -q "Up" || (echo "❌ Kafka stack not running. Start it with 'make kafka-up'" && exit 1)
	@echo "✅ Kafka stack is running"
	@echo ""
	@echo "Starting service..."
	@cd example_service && \
		KAFKA_BOOTSTRAP_SERVERS=localhost:9092 \
		KAFKA_ENABLE_OUTBOX=true \
		KAFKA_ENABLE_INBOX=true \
		python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Complete Kafka setup (stack + dependencies + application)
kafka-all: kafka-up install-messaging
	@echo ""
	@echo "⏳ Waiting for Kafka to initialize (30 seconds)..."
	@sleep 30
	@echo ""
	@echo "🚀 Starting application with Kafka..."
	@$(MAKE) run-with-kafka