# Redis Cache API Demo

FastAPI application demonstrating Redis caching features with interactive API endpoints.

## 🚀 Quick Start

### 1. Start Redis

```bash
docker-compose -f docker-compose.redis.yml up -d
```

### 2. Start the API

```bash
python demo_redis_api.py
```

The API will be available at:
- **API**: http://localhost:8002
- **Interactive Docs (Swagger)**: http://localhost:8002/docs
- **Alternative Docs (ReDoc)**: http://localhost:8002/redoc

### 3. Test the API

```bash
python test_redis_api.py
```

Or use the interactive Swagger UI at http://localhost:8002/docs

---

## 📚 API Endpoints

### Basic Cache Operations

#### Set Cache Value
```bash
curl -X POST http://localhost:8002/cache \
  -H "Content-Type: application/json" \
  -d '{"key": "hello", "value": "world", "ttl": 300}'
```

#### Get Cache Value
```bash
curl http://localhost:8002/cache/hello
```

#### Delete Cache Value
```bash
curl -X DELETE http://localhost:8002/cache/hello
```

#### List All Keys
```bash
curl http://localhost:8002/cache
```

---

### User Profile Caching (Hash Operations)

#### Create User Profile
```bash
curl -X POST http://localhost:8002/users \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "name": "John Doe",
    "email": "john@example.com",
    "age": 30,
    "city": "San Francisco"
  }'
```

#### Get User Profile
```bash
curl http://localhost:8002/users/user123
```

#### Delete User Profile
```bash
curl -X DELETE http://localhost:8002/users/user123
```

---

### Rate Limiting (Lua Script)

#### Check Rate Limit
```bash
curl "http://localhost:8002/rate-limit/check?user_id=user123&limit=10&window=60"
```

This endpoint demonstrates:
- Atomic Lua script execution
- Rate limiting (10 requests per 60 seconds by default)
- Automatic TTL management

Make 10+ requests to see rate limiting in action!

---

### Distributed Locking

#### Process with Lock
```bash
curl -X POST "http://localhost:8002/lock/payment_gateway?processing_time=2"
```

This endpoint demonstrates:
- Distributed lock acquisition
- Only one process can hold the lock
- Automatic lock release after processing
- Concurrent requests will fail with HTTP 409

Try running two requests simultaneously to see locking behavior!

---

### Task Queue (List Operations)

#### Add Task to Queue
```bash
curl -X POST http://localhost:8002/queue/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "id": "task1",
    "title": "Send email",
    "description": "Send welcome email to new user",
    "priority": "high"
  }'
```

#### Get Next Task (FIFO)
```bash
curl http://localhost:8002/queue/tasks
```

#### View All Tasks (without removing)
```bash
curl http://localhost:8002/queue/tasks/all
```

#### Clear Queue
```bash
curl -X DELETE http://localhost:8002/queue/tasks
```

---

### Cache Statistics

#### Get Stats
```bash
curl http://localhost:8002/stats
```

Returns:
- Connection status
- Total keys count
- Memory usage
- Uptime
- Operations per second

#### Reset Demo Data
```bash
curl -X POST http://localhost:8002/stats/reset
```

⚠️ This deletes all keys with the `demo_api:` prefix.

---

## 🎯 Features Demonstrated

### 1. **Basic Cache Operations**
- ✅ Set value with TTL
- ✅ Get value
- ✅ Delete value
- ✅ List keys with pattern matching
- ✅ Key expiration

### 2. **Hash Operations** (User Profiles)
- ✅ Store structured data
- ✅ Field-level access
- ✅ Hash expiration
- ✅ Cache hit/miss tracking

### 3. **Lua Script Execution** (Rate Limiting)
- ✅ Atomic operations
- ✅ Custom business logic in Redis
- ✅ Rate limiting pattern
- ✅ Automatic key expiration

### 4. **Distributed Locking**
- ✅ Cross-process synchronization
- ✅ Lock timeout
- ✅ Automatic lock release
- ✅ Concurrent access prevention

### 5. **List Operations** (Task Queue)
- ✅ FIFO queue
- ✅ Push/Pop operations
- ✅ Queue inspection
- ✅ Batch processing

### 6. **Monitoring & Stats**
- ✅ Connection health check
- ✅ Memory usage tracking
- ✅ Performance metrics
- ✅ Key count

---

## 💡 Usage Examples

### Example 1: User Profile Caching

```python
import requests

# Create user
response = requests.post("http://localhost:8002/users", json={
    "user_id": "alice",
    "name": "Alice Smith",
    "email": "alice@example.com"
})
print(response.json())
# {'message': 'User profile cached successfully', 'user_id': 'alice', ...}

# Get user (cache hit)
response = requests.get("http://localhost:8002/users/alice")
print(response.json())
# {'user_id': 'alice', 'profile': {...}, 'cache_hit': True, 'ttl_seconds': 3599}
```

### Example 2: Rate Limiting

```python
import requests

# Check rate limit (10 requests per minute)
for i in range(12):
    response = requests.get("http://localhost:8002/rate-limit/check", params={
        "user_id": "user123",
        "limit": 10,
        "window": 60
    })
    data = response.json()
    if data["allowed"]:
        print(f"Request {i+1}: ✅ Allowed ({data['current_count']}/10)")
    else:
        print(f"Request {i+1}: ⛔ Rate limited ({data['current_count']}/10)")
```

### Example 3: Task Queue

```python
import requests

# Add tasks
tasks = [
    {"id": "1", "title": "Send email", "priority": "high"},
    {"id": "2", "title": "Process payment", "priority": "high"},
    {"id": "3", "title": "Generate report", "priority": "low"}
]

for task in tasks:
    requests.post("http://localhost:8002/queue/tasks", json=task)

# Process tasks (FIFO)
while True:
    response = requests.get("http://localhost:8002/queue/tasks")
    if response.status_code == 404:
        break
    task = response.json()["task"]
    print(f"Processing: {task['title']}")
```

---

## 🔧 Configuration

Edit `demo_redis_api.py` to change Redis configuration:

```python
redis_config = RedisConfig(
    host="localhost",
    port=6379,
    key_prefix="demo_api:",
    default_ttl=3600,
    max_connections=20
)
```

---

## 📖 API Documentation

The API includes **automatic interactive documentation** powered by FastAPI:

### Swagger UI (Recommended)
**URL**: http://localhost:8002/docs

Features:
- Try out all endpoints directly in the browser
- See request/response schemas
- Auto-generated examples
- Authentication support

### ReDoc
**URL**: http://localhost:8002/redoc

Features:
- Clean, readable documentation
- Searchable
- Multiple language examples
- Downloadable OpenAPI spec

---

## 🎓 Learning Resources

Each endpoint demonstrates a specific Redis pattern:

1. **`/cache/*`** → Basic key-value operations
2. **`/users/*`** → Hash operations for structured data
3. **`/rate-limit/*`** → Lua scripts for atomic operations
4. **`/lock/*`** → Distributed locking pattern
5. **`/queue/*`** → List operations for queues
6. **`/stats`** → Monitoring and health checks

---

## 🐛 Troubleshooting

### API won't start
```bash
# Check if port 8002 is in use
lsof -i :8002

# Kill process if needed
kill -9 <PID>
```

### Cannot connect to Redis
```bash
# Check if Redis is running
docker ps | grep redis

# Check Redis logs
docker logs redis

# Start Redis
docker-compose -f docker-compose.redis.yml up -d
```

### Redis connection refused
```bash
# Test Redis directly
docker exec -it redis redis-cli ping
# Should return: PONG
```

---

## 📊 Performance Tips

1. **Use Pipeline** for batch operations
2. **Set appropriate TTLs** to prevent memory bloat
3. **Use Lua scripts** for atomic multi-step operations
4. **Monitor memory usage** via `/stats` endpoint
5. **Use key prefixes** for namespace isolation

---

## 🎯 Next Steps

1. ✅ Explore the interactive docs at http://localhost:8002/docs
2. ✅ Run the test suite: `python test_redis_api.py`
3. ✅ Try the demo script: `python demo_redis_cache.py`
4. ✅ Read the full documentation: [REDIS_CACHE.md](REDIS_CACHE.md)
5. ✅ Integrate caching in your own application

---

## 🚀 Production Considerations

When deploying to production:

1. **Change key prefix**: Use environment-specific prefixes
2. **Secure Redis**: Enable authentication with `requirepass`
3. **Use SSL/TLS**: Enable encryption for data in transit
4. **Set memory limits**: Configure `maxmemory` in Redis
5. **Monitor performance**: Track cache hit rates and memory usage
6. **Use Redis Sentinel**: For high availability
7. **Backup data**: Enable Redis persistence (AOF/RDB)

See [REDIS_CACHE.md](REDIS_CACHE.md) for detailed production guidelines.
