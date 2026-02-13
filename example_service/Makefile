# Makefile for Example Service
# Convenient commands for running the example service

.PHONY: help install run test clean docker-build docker-run docker-stop docker-deploy

help:
	@echo "Example Service - Available Commands"
	@echo "====================================="
	@echo ""
	@echo "Local Development:"
	@echo "  make install         - Install dependencies"
	@echo "  make run             - Run the service (like: dotnet run)"
	@echo "  make restart         - Kill existing process and restart"
	@echo "  make test            - Run tests"
	@echo "  make stop            - Stop the running service"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make docker-build    - Build Docker image"
	@echo "  make docker-run      - Run application in Docker"
	@echo "  make docker-deploy   - Build and run in Docker (full deploy)"
	@echo "  make docker-stop     - Stop and remove Docker containers"
	@echo "  make docker-logs     - View Docker container logs"
	@echo "  make docker-shell    - Open shell in running container"
	@echo ""
	@echo "Docker Compose:"
	@echo "  make compose-up      - Start services with docker-compose"
	@echo "  make compose-down    - Stop and remove compose services"
	@echo "  make compose-logs    - View compose logs"
	@echo ""
	@echo "Utility:"
	@echo "  make clean           - Clean cache files"
	@echo ""

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	python3 -m pip install -r requirements.txt
	@echo "✅ Dependencies installed!"

# Run the service (equivalent to dotnet run)
run:
	@echo "🚀 Starting User Management Service..."
	@echo ""
	@echo "Service available at:"
	@echo "  - API: http://localhost:8000"
	@echo "  - Docs: http://localhost:8000/docs"
	@echo "  - ReDoc: http://localhost:8000/redoc"
	@echo ""
	python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Stop the running service
stop:
	@echo "🛑 Stopping service..."
	@lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "No process running on port 8000"
	@echo "✅ Service stopped!"

# Restart the service (kill and run)
restart: stop
	@echo "🔄 Restarting service..."
	@sleep 1
	@echo "🚀 Starting User Management Service..."
	@echo ""
	@echo "Service available at:"
	@echo "  - API: http://localhost:8000"
	@echo "  - Docs: http://localhost:8000/docs"
	@echo "  - ReDoc: http://localhost:8000/redoc"
	@echo ""
	python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run in production mode
run-prod:
	@echo "🚀 Starting User Management Service (Production)..."
	python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Run tests
test:
	@echo "🧪 Running tests..."
	pytest tests/ -v

# Clean cache files
clean:
	@echo "🧹 Cleaning cache files..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "✅ Clean complete!"

# Docker commands
docker-build:
	@echo "🐳 Building Docker image..."
	@echo "Note: Building from parent directory to include package source"
	@cd .. && docker build -t user-management-service:latest -f Dockerfile .
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
	@sleep 2
	@echo ""
	@echo "Testing endpoint..."
	@curl -s http://localhost:8000/api/v1/users/ || echo "Service starting up..."

docker-stop:
	@echo "🛑 Stopping Docker container..."
	@docker stop user-management-api 2>/dev/null || echo "Container not running"
	@docker rm user-management-api 2>/dev/null || echo "Container already removed"
	@echo "✅ Container stopped and removed!"

docker-logs:
	@echo "📋 Container logs:"
	@echo "=================="
	docker logs -f user-management-api

docker-shell:
	@echo "🐚 Opening shell in container..."
	docker exec -it user-management-api /bin/bash

# Docker Compose commands
compose-up:
	@echo "🐳 Starting services with docker-compose..."
	docker-compose up -d
	@echo "✅ Services started!"
	@echo ""
	@echo "Service available at:"
	@echo "  - API: http://localhost:8000"
	@echo "  - Docs: http://localhost:8000/docs"

 compose-down:
	@echo "🛑 Stopping docker-compose services..."
	docker-compose down
	@echo "✅ Services stopped!"

compose-logs:
	@echo "📋 Viewing compose logs:"
	docker-compose logs -f

compose-restart: compose-down compose-up
	@echo "✅ Services restarted!"
