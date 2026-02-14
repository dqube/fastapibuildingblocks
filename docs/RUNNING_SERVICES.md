# Running Services

All services are deployed and running successfully! 🎉

## 📊 Service Status

| Service | Status | Port | URL |
|---------|--------|------|-----|
| **User Management API** | ✅ Healthy | 8000 | http://localhost:8000 |
| **API Documentation (Swagger)** | ✅ Running | 8000 | http://localhost:8000/docs |
| **API Documentation (ReDoc)** | ✅ Running | 8000 | http://localhost:8000/redoc |
| **PostgreSQL Database** | ✅ Healthy | 5432 | localhost:5432 |
| **pgAdmin** | ✅ Running | 5050 | http://localhost:5050 |
| **Redis Cache** | ✅ Healthy | 6379 | localhost:6379 |
| **RedisInsight (Redis UI)** | ✅ Running | 5540 | http://localhost:5540 |
| **Kafka** | ✅ Healthy | 9092, 29092 | localhost:9092 |
| **Zookeeper** | ✅ Running | 2181 | localhost:2181 |
| **Grafana** | ✅ Running | 3000 | http://localhost:3000 |
| **Prometheus** | ✅ Running | 9090 | http://localhost:9090 |
| **Tempo (Traces)** | ✅ Running | 3200 | http://localhost:3200 |
| **Loki (Logs)** | ✅ Running | 3100 | http://localhost:3100 |
| **OTEL Collector** | ✅ Running | 4317, 4318 | localhost:4317 |

---

## 🚀 Quick Access

### Primary Application
```bash
# API Homepage
curl http://localhost:8000/

# Get Users
curl http://localhost:8000/api/v1/users/

# Interactive API Docs
open http://localhost:8000/docs

# Test Redis endpoints
./test_redis_endpoints.sh
```

### Redis Testing Endpoints

The application now includes comprehensive Redis testing endpoints:

#### Basic Cache Operations
```bash
# Set cache value
curl -X POST http://localhost:8000/api/v1/redis/cache \
  -H "Content-Type: application/json" \
  -d '{"key": "mykey", "value": "myvalue", "ttl": 300}'

# Get cache value
curl http://localhost:8000/api/v1/redis/cache/mykey

# Delete cache value
curl -X DELETE http://localhost:8000/api/v1/redis/cache/mykey

# List all keys
curl "http://localhost:8000/api/v1/redis/cache?pattern=*&limit=100"
```

#### User Profiles (Hash Operations)
```bash
# Create user profile
curl -X POST http://localhost:8000/api/v1/redis/users \
  -H "Content-Type: application/json" \
  -d '{"user_id": "alice", "name": "Alice Smith", "email": "alice@example.com"}'

# Get user profile
curl http://localhost:8000/api/v1/redis/users/alice

# Delete user profile
curl -X DELETE http://localhost:8000/api/v1/redis/users/alice
```

#### Rate Limiting (Lua Script)
```bash
# Check rate limit (10 requests per 60 seconds)
curl -X POST http://localhost:8000/api/v1/redis/rate-limit/check \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "limit": 10, "window": 60}'
```

#### Task Queue (List Operations)
```bash
# Add task
curl -X POST http://localhost:8000/api/v1/redis/queue/tasks \
  -H "Content-Type: application/json" \
  -d '{"id": "1", "title": "Send email", "priority": "high"}'

# Get next task (FIFO)
curl http://localhost:8000/api/v1/redis/queue/tasks

# View all tasks
curl http://localhost:8000/api/v1/redis/queue/tasks/all

# Clear queue
curl -X DELETE http://localhost:8000/api/v1/redis/queue/tasks
```

#### Distributed Locking
```bash
# Acquire lock and simulate processing
curl -X POST "http://localhost:8000/api/v1/redis/lock/resource_name?processing_time=2"
```

#### Statistics
```bash
# Get Redis statistics
curl http://localhost:8000/api/v1/redis/stats

# Health check
curl http://localhost:8000/api/v1/redis/health

# Reset demo data
curl -X POST http://localhost:8000/api/v1/redis/stats/reset
```

**Run All Tests:**
```bash
./test_redis_endpoints.sh
```

### Database Management
```bash
# pgAdmin (Web UI)
open http://localhost:5050
# Login: admin@admin.com / admin
# Server: postgres-db:5432
# Database: user_management
# User: postgres / postgres

# Direct PostgreSQL Connection
psql postgresql://postgres:postgres@localhost:5432/user_management
```

### Observability

#### Grafana (Dashboards)
```bash
open http://localhost:3000
# No login required (anonymous admin)
```

**Available Dashboards:**
- Application metrics
- System performance
- Database monitoring
- Kafka metrics

**Data Sources:**
- Prometheus (metrics)
- Tempo (distributed tracing)
- Loki (logs)

#### Prometheus (Metrics)
```bash
open http://localhost:9090
```

**Useful Queries:**
```promql
# API request rate
rate(http_requests_total[5m])

# API latency (p95)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Database connections
pg_stat_database_numbackends
```

#### Tempo (Traces)
```bash
# Query endpoint
curl http://localhost:3200/api/search

# View in Grafana
open http://localhost:3000/explore?left=[%22tempo%22]
```

---

## 🧪 Testing the API

### Basic Operations

#### Create User
```bash
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "first_name": "Alice",
    "last_name": "Smith",
    "bio": "Full-stack developer"
  }'
```

#### Get All Users
```bash
curl http://localhost:8000/api/v1/users/
```

#### Get User by ID
```bash
# Replace {user_id} with actual ID from previous response
curl http://localhost:8000/api/v1/users/{user_id}
```

#### Update User
```bash
curl -X PUT http://localhost:8000/api/v1/users/{user_id} \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice.smith@example.com",
    "first_name": "Alice",
    "last_name": "Smith-Johnson",
    "bio": "Senior Full-stack developer"
  }'
```

#### Delete User
```bash
curl -X DELETE http://localhost:8000/api/v1/users/{user_id}
```

---

## 📦 Architecture

### Application Stack
- **API**: FastAPI with DDD architecture (Domain-Driven Design)
- **Database**: PostgreSQL 16 with async support
- **Message Broker**: Kafka with Zookeeper
- **Cache**: Redis with Lua script support

### Building Blocks Features Used
✅ **Exception Handler** - RFC 7807 ProblemDetails
✅ **HTTP Client** - External API communication with 7 auth strategies
✅ **Redis Cache** - Distributed caching with Lua scripts
✅ **Mediator Pattern** - CQRS with commands/queries
✅ **Inbox/Outbox Pattern** - Transactional messaging
✅ **Observability** - OpenTelemetry tracing, metrics, and logs

### Observability Stack
- **Traces**: OpenTelemetry → OTEL Collector → Tempo
- **Logs**: Application → Promtail → Loki
- **Metrics**: Application → Prometheus
- **Visualization**: Grafana (all data sources)

---

## 🔧 Management Commands

### Docker Compose

#### View Logs
```bash
# All services
cd example_service && docker-compose logs -f

# Specific service
docker logs -f user-management-api
docker logs -f postgres-db
docker logs -f kafka
```

#### Restart Services
```bash
# All services
cd example_service && docker-compose restart

# Specific service
docker restart user-management-api
```

#### Stop Services
```bash
cd example_service && docker-compose down
```

#### Rebuild and Restart
```bash
cd example_service && docker-compose up -d --build
```

### Redis Cache

Redis is running separately with RedisInsight UI. To manage:

```bash
# Open RedisInsight (Web UI)
open http://localhost:5540

# Stop Redis + UI
docker-compose -f docker-compose.redis.yml down

# Start Redis + UI
docker-compose -f docker-compose.redis.yml up -d

# Access Redis CLI
docker exec -it redis redis-cli

# Test Redis
docker exec -it redis redis-cli ping
# Should return: PONG
```

**RedisInsight Features:**
- Visual key browser
- Execute commands
- Real-time monitoring
- Memory analysis
- Cluster management
- Pub/Sub monitoring

---

## 📊 Health Checks

### API Health
```bash
curl http://localhost:8000/health
```

### Database Health
```bash
docker exec -it postgres-db pg_isready -U postgres
# Should return: accepting connections
```

### Kafka Health
```bash
docker exec -it kafka kafka-broker-api-versions --bootstrap-server localhost:9092
```

### Redis Health
```bash
docker exec -it redis redis-cli ping
# Should return: PONG
```

---

## 🐛 Troubleshooting

### API not responding
```bash
# Check API logs
docker logs -f user-management-api

# Check API health
docker exec -it user-management-api curl http://localhost:8000/api/v1/users/
```

### Database connection issues
```bash
# Check PostgreSQL logs
docker logs -f postgres-db

# Verify connection
docker exec -it postgres-db psql -U postgres -d user_management -c "SELECT 1;"
```

### Port conflicts
```bash
# Check what's using port 8000
lsof -i :8000

# Kill process if needed
lsof -ti :8000 | xargs kill -9
```

### Container issues
```bash
# Remove all stopped containers
docker container prune

# Remove all unused volumes
docker volume prune

# Full cleanup and restart
cd example_service
docker-compose down -v
docker-compose up -d --build
```

---

## 📚 Documentation

- [Getting Started](GETTING_STARTED.md)
- [Exception Handler](EXCEPTION_HANDLER.md)
- [HTTP Client](HTTP_CLIENT.md)
- [Redis Cache](REDIS_CACHE.md)
- [Redis API Guide](REDIS_API_GUIDE.md)
- [Kafka Integration](KAFKA_INTEGRATION.md)
- [Observability](OBSERVABILITY.md)
- [Mediator Pattern](MEDIATOR_PATTERN.md)
- [Inbox/Outbox Pattern](INBOX_OUTBOX_PATTERN.md)

---

## 🎯 Next Steps

1. **Explore the API** → http://localhost:8000/docs
2. **View Metrics** → http://localhost:3000 (Grafana)
3. **Check Logs** → `docker logs -f user-management-api`
4. **Test Features** → See [GETTING_STARTED.md](GETTING_STARTED.md)
5. **Build Your App** → Use the building_blocks package

---

## 📝 Environment Variables

The application is configured via environment variables in `docker-compose.yml`:

```yaml
DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/user_management
OTEL_SERVICE_NAME: user-management-api
OTEL_EXPORTER_OTLP_ENDPOINT: http://otel-collector:4317
KAFKA_BOOTSTRAP_SERVERS: kafka:9092
KAFKA_CONSUMER_GROUP: user-management-api-group
```

To customize, edit `example_service/docker-compose.yml` and restart services.

---

## 🔒 Security Notes

**⚠️ For development only!**

This setup uses default credentials and is not secured for production use:

- PostgreSQL: `postgres/postgres`
- pgAdmin: `admin@admin.com/admin`
- Grafana: Anonymous admin access
- Redis: No authentication

For production:
1. Change all passwords
2. Enable TLS/SSL
3. Use secrets management
4. Enable authentication on all services
5. Configure firewalls
6. Use environment-specific configs

---

## 📞 Support

If you encounter any issues:

1. Check logs: `docker-compose logs -f`
2. Verify health: `docker ps`
3. Review documentation in the root directory
4. Check container status: `docker-compose ps`

---

**Status**: ✅ All systems operational
**Last Updated**: February 14, 2026
**Environment**: Development (Docker Compose)
