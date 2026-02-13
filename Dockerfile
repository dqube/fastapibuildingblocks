# Multi-stage Dockerfile for FastAPI Building Blocks Example Service
# Build from project root directory

# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy the building blocks package
COPY src ./src
COPY pyproject.toml README.md ./

# Install the building blocks package
RUN pip install --no-cache-dir --user .

# Copy example service requirements
COPY example_service/requirements.txt ./

# Install remaining dependencies (excluding the local package)
RUN grep -v "fastapi-building-blocks" requirements.txt > requirements-docker.txt || echo "" > requirements-docker.txt && \
    if [ -s requirements-docker.txt ]; then pip install --no-cache-dir --user -r requirements-docker.txt; fi

# Stage 2: Runtime
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy example service application code
COPY --chown=appuser:appuser example_service/ .

# Switch to non-root user
USER appuser

# Add local bin to PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/users/')"

# Run the application
CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
