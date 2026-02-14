# Redis Cache Implementation

Comprehensive Redis caching implementation with Lua script support, distributed locking, and external API configuration.

## 📋 Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Basic Operations](#basic-operations)
- [Data Structures](#data-structures)
- [Lua Scripts](#lua-scripts)
- [Distributed Locking](#distributed-locking)
- [Pipeline Operations](#pipeline-operations)
- [Cache Decorator](#cache-decorator)
- [External API Configuration](#external-api-configuration)
- [Integration Patterns](#integration-patterns)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## ✨ Features

### Core Redis Features
- ✅ **Async/await support** - Built on `redis-py` async client
- ✅ **Connection pooling** - Efficient connection management
- ✅ **Automatic serialization** - JSON and Pickle support
- ✅ **Key prefixing** - Namespace isolation
- ✅ **TTL management** - Automatic expiration
- ✅ **Health checking** - Connection monitoring

### Advanced Features
- ✅ **Lua script execution** - Custom atomic operations
- ✅ **Distributed locking** - Cross-process synchronization
- ✅ **Pipeline operations** - Batch command execution
- ✅ **Cache decorator** - Function result caching
- ✅ **Multiple data structures** - Strings, Hashes, Lists, Sets
- ✅ **External API configuration** - Centralized API settings

### Production-Ready
- ✅ **Error handling** - Graceful degradation
- ✅ **Logging** - Structured logging throughout
- ✅ **Configurable** - All settings externalized
- ✅ **Type hints** - Full type safety
- ✅ **Context managers** - Automatic cleanup

---

## 📦 Installation

### Install Dependencies

```bash
pip install redis[hiredis]
```

Add to `pyproject.toml`:

```toml
[project]
dependencies = [
    "redis[hiredis]>=5.0.0",
]
```

### Start Redis Server

**Using Docker:**
```bash
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7-alpine
```

**Using Docker Compose** (`docker-compose.yml`):
```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

volumes:
  redis_data:
```

---

## 🚀 Quick Start

### Basic Usage

```python
from building_blocks.infrastructure.cache import RedisClient, RedisConfig

# Configure client
config = RedisConfig(
    host="localhost",
    port=6379,
    key_prefix="myapp:",
    default_ttl=3600  # 1 hour
)

# Use with context manager
async with RedisClient(config) as cache:
    # Set value
    await cache.set("user:123", {"name": "John", "email": "john@example.com"})
    
    # Get value
    user = await cache.get("user:123")
    print(user)  # {'name': 'John', 'email': 'john@example.com'}
    
    # Delete
    await cache.delete("user:123")
```

### Manual Connection Management

```python
cache = RedisClient(config)
await cache.connect()

try:
    await cache.set("key", "value")
    value = await cache.get("key")
finally:
    await cache.disconnect()
```

---

## ⚙️ Configuration

### RedisConfig Options

```python
from building_blocks.infrastructure.cache import RedisConfig

config = RedisConfig(
    # Connection settings
    host="localhost",
    port=6379,
    db=0,
    password=None,              # Redis AUTH password
    username=None,              # Redis 6+ ACL username
    
    # Connection pool
    max_connections=50,
    socket_timeout=5.0,
    socket_connect_timeout=5.0,
    socket_keepalive=True,
    
    # Retry settings
    retry_on_timeout=True,
    retry_on_error=True,
    max_retry_attempts=3,
    
    # SSL/TLS (for production)
    ssl=False,
    ssl_cert_reqs="required",
    ssl_ca_certs="/path/to/ca-cert.pem",
    ssl_certfile="/path/to/client-cert.pem",
    ssl_keyfile="/path/to/client-key.pem",
    
    # Cache settings
    default_ttl=3600,           # Default expiration (seconds)
    key_prefix="myapp:",        # Prefix all keys
    
    # Encoding
    encoding="utf-8",
    decode_responses=True,      # Decode byte responses to strings
    
    # Health check
    health_check_interval=30,   # Seconds between health checks
    
    # Cluster mode (advanced)
    cluster_enabled=False,
    cluster_nodes=[],
    
    # Sentinel mode (high availability)
    sentinel_enabled=False,
    sentinel_nodes=[],
    sentinel_master_name=None
)
```

### Environment Variables

```bash
# .env file
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-password
REDIS_DB=0
REDIS_KEY_PREFIX=myapp:
REDIS_DEFAULT_TTL=3600
```

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None
    REDIS_DB: int = 0
    REDIS_KEY_PREFIX: str = ""
    REDIS_DEFAULT_TTL: int = 3600
    
    class Config:
        env_file = ".env"

settings = Settings()

redis_config = RedisConfig(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    db=settings.REDIS_DB,
    key_prefix=settings.REDIS_KEY_PREFIX,
    default_ttl=settings.REDIS_DEFAULT_TTL
)
```

---

## 📝 Basic Operations

### Set and Get

```python
# Set with default TTL
await cache.set("user:123", {"name": "John"})

# Set with custom TTL
await cache.set("session:abc", {"user_id": 123}, ttl=300)  # 5 minutes

# Set only if not exists (nx)
success = await cache.set("lock:resource", "locked", nx=True)

# Set only if exists (xx)
success = await cache.set("counter", 100, xx=True)

# Get value
user = await cache.get("user:123")

# Get with default
value = await cache.get("missing_key", default="fallback")
```

### Delete and Expire

```python
# Delete single key
await cache.delete("user:123")

# Delete multiple keys
count = await cache.delete("user:123", "user:456", "user:789")

# Set expiration
await cache.expire("session:abc", 600)  # 10 minutes

# Check TTL
ttl = await cache.ttl("session:abc")  # Returns seconds remaining
```

### Exists and Keys

```python
# Check if keys exist
count = await cache.exists("user:123", "user:456")  # Returns 0-2

# Get all keys matching pattern (⚠️ use with caution in production)
keys = await cache.keys("user:*")

# Scan keys (better for production - cursor-based)
async for key in cache.scan_iter(match="user:*", count=100):
    print(key)
```

### Increment and Decrement

```python
# Counter operations
await cache.set("views", 0)
await cache.increment("views")          # views = 1
await cache.increment("views", 10)      # views = 11
await cache.decrement("views", 5)       # views = 6

final_count = await cache.get("views")  # 6
```

---

## 🗂️ Data Structures

### Hashes (Objects)

Perfect for storing structured data like user profiles, settings, etc.

```python
# Set individual fields
await cache.hset("profile:123", "name", "Alice")
await cache.hset("profile:123", "email", "alice@example.com")
await cache.hset("profile:123", "age", 30)

# Get single field
name = await cache.hget("profile:123", "name")

# Get all fields
profile = await cache.hgetall("profile:123")
# {'name': 'Alice', 'email': 'alice@example.com', 'age': 30}

# Delete fields
await cache.hdel("profile:123", "age")
```

### Lists (Queues)

Perfect for task queues, event logs, etc.

```python
# Push to tail (enqueue)
await cache.rpush("tasks", {"id": 1, "task": "Send email"})
await cache.rpush("tasks", {"id": 2, "task": "Process order"})

# Push to head
await cache.lpush("tasks", {"id": 0, "urgent": "Critical task"})

# Pop from head (dequeue - FIFO)
task = await cache.lpop("tasks")

# Pop from tail (LIFO)
task = await cache.rpop("tasks")

# View range without removing
tasks = await cache.lrange("tasks", 0, 9)  # First 10 tasks
```

### Sets (Unique Collections)

Perfect for tags, permissions, active users, etc.

```python
# Add members
await cache.sadd("tags:post:123", "python", "redis", "caching")

# Add duplicate (ignored)
await cache.sadd("tags:post:123", "python")  # No effect

# Get all members
tags = await cache.smembers("tags:post:123")
# {'python', 'redis', 'caching'}

# Check membership
has_python = await cache.sismember("tags:post:123", "python")  # True

# Remove member
await cache.srem("tags:post:123", "caching")
```

---

## 🔧 Lua Scripts

Lua scripts execute atomically on the Redis server, ensuring consistency.

### Example 1: Rate Limiting

```python
# Rate limiting script
rate_limit_script = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])

local current = redis.call('GET', key)

if current and tonumber(current) >= limit then
    return 0  -- Rate limit exceeded
else
    redis.call('INCR', key)
    if not current then
        redis.call('EXPIRE', key, window)
    end
    return 1  -- Request allowed
end
"""

# Register script
cache.register_script("rate_limit", rate_limit_script)

# Execute script
allowed = await cache.execute_script(
    "rate_limit",
    keys=["rate:user:123"],
    args=[10, 60]  # 10 requests per 60 seconds
)

if allowed:
    print("Request allowed")
else:
    print("Rate limit exceeded")
```

### Example 2: Atomic Check-and-Set

```python
check_and_set = """
local key = KEYS[1]
local expected = ARGV[1]
local new_value = ARGV[2]

local current = redis.call('GET', key)

if current == expected then
    redis.call('SET', key, new_value)
    return 1  -- Success
else
    return 0  -- Failed (value changed)
end
"""

# Direct execution (no registration needed)
success = await cache.eval(
    check_and_set,
    keys=["inventory:item123"],
    args=["10", "9"]  # Expected 10, set to 9
)
```

### Example 3: Atomic Counter with Metadata

```python
counter_with_ttl = """
local key = KEYS[1]
local amount = tonumber(ARGV[1])

local new_value = redis.call('INCRBY', key, amount)
local ttl = redis.call('TTL', key)

return {new_value, ttl}
"""

result = await cache.eval(
    counter_with_ttl,
    keys=["counter:api_calls"],
    args=[1]
)

new_value, ttl = result
print(f"Counter: {new_value}, TTL: {ttl}s")
```

---

## 🔒 Distributed Locking

Ensure only one process accesses a resource at a time.

### Basic Lock

```python
async with cache.lock("order-processing", timeout=10.0):
    # Critical section - only one process can execute this
    order = await process_order()
    await send_confirmation_email()
    # Lock automatically released
```

### Lock with Timeout

```python
try:
    async with cache.lock(
        "report-generation",
        timeout=30.0,           # Lock expires after 30s
        blocking_timeout=5.0    # Wait max 5s to acquire lock
    ):
        await generate_expensive_report()
except Exception as e:
    print(f"Failed to acquire lock: {e}")
```

### Concurrent Workers Example

```python
async def worker(worker_id: int):
    try:
        async with cache.lock("shared-resource", timeout=5.0, blocking_timeout=2.0):
            print(f"Worker {worker_id}: Processing...")
            await asyncio.sleep(1)
            print(f"Worker {worker_id}: Done")
    except Exception as e:
        print(f"Worker {worker_id}: {e}")

# Run 5 workers concurrently (only one will hold lock at a time)
await asyncio.gather(
    *[worker(i) for i in range(5)]
)
```

---

## 🚀 Pipeline Operations

Batch multiple commands for better performance.

### Basic Pipeline

```python
async with cache.pipeline() as pipe:
    pipe.set("key1", "value1")
    pipe.set("key2", "value2")
    pipe.set("key3", "value3")
    pipe.get("key1")
    pipe.get("key2")
    
    # Execute all commands at once
    results = await pipe.execute()
    # [True, True, True, 'value1', 'value2']
```

### Transaction Pipeline

```python
# Atomic execution with MULTI/EXEC
async with cache.pipeline(transaction=True) as pipe:
    pipe.get("counter")
    pipe.incr("counter")
    pipe.expire("counter", 3600)
    
    results = await pipe.execute()
```

### Bulk Operations

```python
# Set 1000 keys efficiently
async with cache.pipeline() as pipe:
    for i in range(1000):
        pipe.set(f"bulk:item:{i}", {"id": i, "value": i * 10})
    
    await pipe.execute()

print("Inserted 1000 items in one round-trip!")
```

---

## 🎯 Cache Decorator

Automatically cache function results.

### Basic Caching

```python
@cache.cached("user:profile:{user_id}", ttl=300)
async def get_user_profile(user_id: int):
    # Expensive operation (database query)
    print(f"Fetching user {user_id} from database...")
    await asyncio.sleep(1)
    return {"id": user_id, "name": f"User {user_id}"}

# First call - cache miss
profile1 = await get_user_profile(123)  # Takes 1 second

# Second call - cache hit
profile2 = await get_user_profile(123)  # Instant!
```

### Multiple Parameters

```python
@cache.cached("product:{category}:{product_id}", ttl=600)
async def get_product(category: str, product_id: int):
    # Fetch from database
    return await db.query(
        "SELECT * FROM products WHERE category = ? AND id = ?",
        category, product_id
    )

# Each unique combination is cached separately
product1 = await get_product("electronics", 123)
product2 = await get_product("books", 456)
```

### Cache Invalidation

```python
# Manual invalidation
await cache.delete("user:profile:123")

# Invalidate with pattern
async for key in cache.scan_iter(match="user:profile:*"):
    await cache.delete(key)
```

---

## 🌐 External API Configuration

Centralized configuration for external API integrations.

### Basic Configuration

```python
from building_blocks.infrastructure.cache import ExternalApiConfig

# Payment API
payment_api = ExternalApiConfig(
    name="stripe",
    base_url="https://api.stripe.com/v1",
    auth_type="bearer",
    bearer_token="sk_test_123456789",
    timeout=30.0,
    max_retries=3,
    enable_circuit_breaker=True,
    enable_caching=True,
    cache_ttl=300,
    consumer_id="payment-service-v1"
)
```

### Authentication Types

```python
# 1. No Authentication
api = ExternalApiConfig(
    name="public-api",
    base_url="https://api.example.com",
    auth_type="none"
)

# 2. Bearer Token
api = ExternalApiConfig(
    name="secured-api",
    base_url="https://api.example.com",
    auth_type="bearer",
    bearer_token="your-token-here"
)

# 3. Basic Authentication
api = ExternalApiConfig(
    name="legacy-api",
    base_url="https://api.example.com",
    auth_type="basic",
    basic_username="admin",
    basic_password="password123"
)

# 4. API Key (Header)
api = ExternalApiConfig(
    name="api-key-service",
    base_url="https://api.example.com",
    auth_type="api_key",
    api_key="your-api-key",
    api_key_header="X-API-Key"
)

# 5. OAuth2 Client Credentials
api = ExternalApiConfig(
    name="oauth-service",
    base_url="https://api.example.com",
    auth_type="oauth2",
    oauth2_token_url="https://oauth2.example.com/token",
    oauth2_client_id="client-id",
    oauth2_client_secret="client-secret",
    oauth2_scope="read write"
)

# 6. Custom Headers
api = ExternalApiConfig(
    name="custom-auth",
    base_url="https://api.example.com",
    auth_type="custom",
    custom_headers={
        "X-Custom-Auth": "secret-key",
        "X-Service-Name": "my-service"
    }
)
```

### Caching and Rate Limiting

```python
api = ExternalApiConfig(
    name="weather-api",
    base_url="https://api.weather.com/v1",
    auth_type="api_key",
    api_key="your-key",
    
    # Enable caching
    enable_caching=True,
    cache_ttl=600,                    # Cache for 10 minutes
    cache_key_prefix="weather:",      # Custom prefix
    
    # Rate limiting
    rate_limit_enabled=True,
    rate_limit_requests=100,          # 100 requests
    rate_limit_period=60,             # Per 60 seconds
    
    # Circuit breaker
    enable_circuit_breaker=True,
    circuit_breaker_threshold=5,      # Open after 5 failures
    circuit_breaker_timeout=60.0      # Try again after 60s
)

# Get cache key prefix
prefix = api.get_cache_key_prefix()  # "weather:"
```

---

## 🔗 Integration Patterns

### Pattern 1: API Response Caching

```python
from building_blocks.infrastructure.cache import RedisClient, RedisConfig, ExternalApiConfig
from building_blocks.infrastructure.http import HttpClient, HttpClientConfig, BearerAuth

# Setup Redis
redis_config = RedisConfig(
    host="localhost",
    port=6379,
    key_prefix="api_cache:"
)

# Setup API
api_config = ExternalApiConfig(
    name="weather-api",
    base_url="https://api.weather.com",
    auth_type="api_key",
    api_key="your-key",
    enable_caching=True,
    cache_ttl=600
)

async def fetch_weather_with_cache(city: str):
    async with RedisClient(redis_config) as cache:
        cache_key = f"{api_config.get_cache_key_prefix()}weather:{city}"
        
        # Check cache
        cached = await cache.get(cache_key)
        if cached:
            return cached
        
        # Fetch from API
        http_config = HttpClientConfig(
            base_url=api_config.base_url,
            auth_strategy=BearerAuth(api_config.api_key),
            timeout=api_config.timeout
        )
        
        async with HttpClient(http_config) as client:
            response = await client.get(f"/weather?city={city}")
            data = response.json()
        
        # Cache result
        await cache.set(cache_key, data, ttl=api_config.cache_ttl)
        return data
```

### Pattern 2: Session Storage

```python
async def create_session(user_id: int, data: dict):
    session_id = str(uuid.uuid4())
    session_key = f"session:{session_id}"
    
    await cache.set(session_key, {
        "user_id": user_id,
        "data": data,
        "created_at": datetime.now().isoformat()
    }, ttl=3600)  # 1 hour
    
    return session_id

async def get_session(session_id: str):
    return await cache.get(f"session:{session_id}")

async def delete_session(session_id: str):
    await cache.delete(f"session:{session_id}")
```

### Pattern 3: Distributed Rate Limiting

```python
async def check_rate_limit(user_id: int, limit: int = 100, window: int = 60):
    """Rate limit: {limit} requests per {window} seconds."""
    
    rate_limit_script = """
    local key = KEYS[1]
    local limit = tonumber(ARGV[1])
    local window = tonumber(ARGV[2])
    local current = redis.call('GET', key)
    
    if current and tonumber(current) >= limit then
        return {0, current}
    else
        local new_count = redis.call('INCR', key)
        if new_count == 1 then
            redis.call('EXPIRE', key, window)
        end
        return {1, new_count}
    end
    """
    
    cache.register_script("rate_limit", rate_limit_script)
    
    result = await cache.execute_script(
        "rate_limit",
        keys=[f"rate_limit:user:{user_id}"],
        args=[limit, window]
    )
    
    allowed, current_count = result
    return bool(allowed), current_count
```

### Pattern 4: Cache-Aside Pattern

```python
async def get_user(user_id: int):
    """Cache-aside pattern for user data."""
    cache_key = f"user:{user_id}"
    
    # 1. Try cache first
    user = await cache.get(cache_key)
    if user:
        return user
    
    # 2. Cache miss - load from database
    user = await db.fetch_user(user_id)
    if not user:
        return None
    
    # 3. Update cache
    await cache.set(cache_key, user, ttl=3600)
    
    return user

async def update_user(user_id: int, data: dict):
    """Update user and invalidate cache."""
    
    # 1. Update database
    await db.update_user(user_id, data)
    
    # 2. Invalidate cache
    await cache.delete(f"user:{user_id}")
    
    # OR update cache directly (write-through)
    # await cache.set(f"user:{user_id}", updated_user, ttl=3600)
```

---

## 💡 Best Practices

### 1. Use Key Prefixes

```python
# Configure key prefix for namespace isolation
config = RedisConfig(
    key_prefix="myapp:prod:",  # or "myapp:dev:"
    # ...
)

# All keys are automatically prefixed
await cache.set("user:123", data)  # Stored as "myapp:prod:user:123"
```

### 2. Set Appropriate TTLs

```python
# Short TTL for frequently changing data
await cache.set("stock_price:AAPL", price, ttl=60)  # 1 minute

# Medium TTL for semi-static data
await cache.set("user:profile:123", profile, ttl=3600)  # 1 hour

# Long TTL for static data
await cache.set("config:app_settings", settings, ttl=86400)  # 24 hours
```

### 3. Handle Cache Misses Gracefully

```python
async def get_data(key: str):
    data = await cache.get(key)
    if data is None:
        # Fallback to database or default value
        data = await fetch_from_database(key)
        if data:
            await cache.set(key, data)
    return data
```

### 4. Use Pipelines for Bulk Operations

```python
# ❌ Slow (N round-trips)
for i in range(1000):
    await cache.set(f"item:{i}", data[i])

# ✅ Fast (1 round-trip)
async with cache.pipeline() as pipe:
    for i in range(1000):
        pipe.set(f"item:{i}", data[i])
    await pipe.execute()
```

### 5. Use Lua Scripts for Atomic Operations

```python
# ❌ Not atomic (race condition possible)
current = await cache.get("counter")
new_value = int(current) + 1
await cache.set("counter", new_value)

# ✅ Atomic (use Lua script or INCR)
await cache.increment("counter")
```

### 6. Monitor Cache Hit Rates

```python
async def get_with_metrics(key: str):
    value = await cache.get(key)
    
    if value is not None:
        metrics.increment("cache.hits")
    else:
        metrics.increment("cache.misses")
    
    return value
```

### 7. Set Reasonable Connection Pool Size

```python
config = RedisConfig(
    max_connections=50,  # Adjust based on concurrency
    # For low-traffic apps: 10-20
    # For high-traffic apps: 50-100
)
```

### 8. Use Scan Instead of Keys in Production

```python
# ❌ Blocks Redis (bad for production)
all_keys = await cache.keys("user:*")

# ✅ Non-blocking cursor-based iteration
async for key in cache.scan_iter(match="user:*", count=100):
    await process_key(key)
```

---

## 🐛 Troubleshooting

### Connection Errors

```python
# Problem: Cannot connect to Redis
# Solution: Check Redis is running and accessible

# Test connection
async with RedisClient(config) as cache:
    if await cache.ping():
        print("✅ Connected to Redis")
    else:
        print("❌ Cannot reach Redis")

# Check Redis server
# $ redis-cli ping
# PONG
```

### Serialization Errors

```python
# Problem: Cannot serialize complex objects
# Solution: Use pickle instead of JSON

# ❌ Fails with custom objects
await cache.set("obj", MyCustomClass(), use_json=True)

# ✅ Works with any Python object
await cache.set("obj", MyCustomClass(), use_json=False)
```

### Memory Issues

```python
# Problem: Redis running out of memory
# Solution: Set TTLs on all keys

# Check memory usage
info = await cache.info("memory")
print(f"Used memory: {info['used_memory_human']}")

# Set eviction policy in redis.conf
# maxmemory 256mb
# maxmemory-policy allkeys-lru
```

### Lua Script Errors

```python
# Problem: Lua script fails
# Solution: Check syntax and test separately

# Test script in redis-cli first
# $ redis-cli
# > EVAL "return redis.call('GET', KEYS[1])" 1 mykey

# Add error handling
try:
    result = await cache.execute_script("my_script", keys=["key"], args=["arg"])
except Exception as e:
    logger.error(f"Lua script failed: {e}")
    # Fallback logic
```

### Lock Timeouts

```python
# Problem: Cannot acquire lock
# Solution: Increase blocking_timeout or check for deadlocks

try:
    async with cache.lock(
        "resource",
        timeout=30.0,
        blocking_timeout=10.0  # Wait longer
    ):
        await process()
except Exception as e:
    logger.warning(f"Lock acquisition failed: {e}")
    # Queue for later or skip
```

---

## 📚 Additional Resources

- [Redis Documentation](https://redis.io/documentation)
- [redis-py Documentation](https://redis-py.readthedocs.io/)
- [Redis Best Practices](https://redis.io/topics/best-practices)
- [Lua Scripting Guide](https://redis.io/commands/eval)

---

## 🎯 Summary

The Redis cache implementation provides:

✅ **Simple API** - Easy to use with async/await  
✅ **Powerful Features** - Lua scripts, locking, pipelines  
✅ **Production-Ready** - Connection pooling, error handling  
✅ **Flexible** - Multiple data structures and serialization  
✅ **Integrated** - Works with external API configuration  

**Next Steps:**
1. Review [demo_redis_cache.py](demo_redis_cache.py) for complete examples
2. Configure Redis in your application settings
3. Integrate with your HTTP client for API caching
4. Monitor cache hit rates and adjust TTLs as needed
