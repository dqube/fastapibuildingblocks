# Makefile for FastAPI Building Blocks
# Similar to dotnet run/build commands

.PHONY: help install dev run test clean build lint format docker-build docker-deploy

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
