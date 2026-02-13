# Docker Quick Reference

## ✅ Docker Support Successfully Added!

Your application now has full Docker support with easy-to-use make commands.

## 🐳 Docker Commands

### From Project Root (`/Users/mdevendran/python/fastapibuildingblocks`)

```bash
# Build Docker image
make docker-build

# Deploy (build + run)
make docker-deploy

# Stop container
make docker-stop

# View logs
make docker-logs

# Run container
make docker-run
```

### From Example Service (`example_service/`)

```bash
# Build from example_service directory
make docker-build        # Builds from parent directory

# Run
make docker-run          # Start the container

# Full deploy (stop, build, run)
make docker-deploy

# Stop
make docker-stop

# View logs
make docker-logs

# Open shell in container
make docker-shell

# Docker Compose
make compose-up          # Start with docker-compose
make compose-down        # Stop compose services
make compose-logs        # View compose logs
make compose-restart     # Restart all services
```

## 📝 What Was Created

### 1. Dockerfiles
- **`/Dockerfile`** - Root level Dockerfile (builds entire app with package)
- **`example_service/Dockerfile`** - Service-specific Dockerfile (legacy)

### 2. Docker Configuration
- **`.dockerignore`** - Excludes unnecessary files from Docker build
- **`docker-compose.yml`** - Compose configuration for easy orchestration

### 3. Makefile Commands
Enhanced Makefiles with Docker support commands.

## 🚀 Quick Start

### Option 1: One Command Deploy
```bash
cd /Users/mdevendran/python/fastapibuildingblocks
make docker-deploy
```

This will:
1. Stop any existing container
2. Build a fresh Docker image
3. Start the container
4. Test the endpoint

### Option 2: Step by Step
```bash
# Build the image
make docker-build

# Run the container
make docker-run

# View logs
make docker-logs
```

### Option 3: Docker Compose
```bash
cd example_service
make compose-up          # Start services
make compose-logs        # View logs
make compose-down        # Stop services
```

## 📊 Current Status

✅ **Container Running:** `user-management-api`  
✅ **Image:** `user-management-service:latest`  
✅ **Status:** Healthy  
✅ **Ports:** 0.0.0.0:8000->8000/tcp

### Access the Application

- **API Endpoint:** http://localhost:8000/api/v1/users/
- **Swagger Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## 🛠️ Docker Features

### Multi-Stage Build
- **Stage 1 (Builder):** Compiles dependencies and installs packages
- **Stage 2 (Runtime):** Minimal runtime environment
- **Result:** Smaller, more secure images

### Security Features
- ✅ Runs as non-root user (`appuser`)
- ✅ Minimal base image (python:3.12-slim)
- ✅ No unnecessary packages
- ✅ Health checks enabled

### Health Checks
The container includes automatic health checks:
```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3
```

## 📦 Docker Image Details

```bash
# View image
docker images user-management-service

# Inspect image
docker inspect user-management-service:latest

# View container logs
docker logs user-management-api

# View container stats
docker stats user-management-api

# Execute command in container
docker exec -it user-management-api python3 --version
```

## 🔧 Troubleshooting

### Container won't start
```bash
# Check logs
make docker-logs

# Or directly
docker logs user-management-api
```

### Port already in use
```bash
# Stop existing container
make docker-stop

# Check what's using port 8000
lsof -i:8000

# Kill process on port 8000
make stop  # stops local development server
```

### Rebuild from scratch
```bash
# Stop and remove container
make docker-stop

# Remove image
docker rmi user-management-service:latest

# Rebuild
make docker-build
```

## 🌐 Environment Variables

You can pass environment variables to the container:

```bash
docker run -d \
  --name user-management-api \
  -p 8000:8000 \
  -e PORT=8000 \
  -e ENVIRONMENT=production \
  user-management-service:latest
```

## 🚢 Production Deployment

### Build for production
```bash
# Build optimized image
make docker-build

# Tag for registry
docker tag user-management-service:latest your-registry/user-management-service:v1.0.0

# Push to registry
docker push your-registry/user-management-service:v1.0.0
```

### Run in production
```bash
docker run -d \
  --name user-management-api \
  --restart unless-stopped \
  -p 8000:8000 \
  -e PORT=8000 \
  your-registry/user-management-service:v1.0.0
```

## 📋 Common Commands Summary

| Command | Description |
|---------|-------------|
| `make docker-deploy` | Full deployment (stop, build, run) |
| `make docker-build` | Build Docker image |
| `make docker-run` | Run container |
| `make docker-stop` | Stop and remove container |
| `make docker-logs` | View container logs |
| `make compose-up` | Start with docker-compose |
| `make compose-down` | Stop docker-compose services |

## ✨ Similar to .NET Commands

| .NET | Python/Docker Equivalent |
|------|-------------------------|
| `dotnet restore` | `make install` |
| `dotnet build` | `make docker-build` |
| `dotnet run` | `make docker-deploy` or `make run` |
| `dotnet test` | `make test` |
| `dotnet publish` | `make docker-build` |

## 🎉 Success!

Your FastAPI Building Blocks application is now containerized and running in Docker with:
- ✅ Multi-stage optimized builds
- ✅ Security best practices
- ✅ Health checks
- ✅ Easy deployment commands
- ✅ Docker Compose support
- ✅ Non-root user execution
- ✅ Minimal attack surface

**Current Test:**
- Created user successfully in Docker container
- User ID: `a214318d-7669-4cd7-bda3-0f70c8d9360c`
- Email: `docker@example.com`
- Container Status: Healthy ✅
