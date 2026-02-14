"""
FastAPI Demo - Redis Cache Features

API endpoints demonstrating Redis caching capabilities:
- Basic cache operations
- User profile caching
- Rate limiting with Lua scripts
- Distributed locking
- Session management
- Task queues
- Cache statistics
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Header
from pydantic import BaseModel, Field

from building_blocks.infrastructure.cache import RedisClient, RedisConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

redis_config = RedisConfig(
    host="localhost",
    port=6379,
    key_prefix="demo_api:",
    default_ttl=3600,
    max_connections=20
)

# Global Redis client
redis_client: Optional[RedisClient] = None


# ============================================================================
# Lifespan Management
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage Redis connection lifecycle."""
    global redis_client
    
    # Startup
    redis_client = RedisClient(redis_config)
    await redis_client.connect()
    
    # Register Lua scripts
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
    redis_client.register_script("rate_limit", rate_limit_script)
    
    logger.info("✅ Redis connected and Lua scripts registered")
    
    yield
    
    # Shutdown
    await redis_client.disconnect()
    logger.info("✅ Redis disconnected")


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="Redis Cache Demo API",
    description="Demonstration of Redis caching features",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================================
# Pydantic Models
# ============================================================================

class CacheItem(BaseModel):
    """Cache item model."""
    key: str
    value: str
    ttl: Optional[int] = Field(None, description="Time to live in seconds")


class UserProfile(BaseModel):
    """User profile model."""
    user_id: str
    name: str
    email: str
    age: Optional[int] = None
    city: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class Task(BaseModel):
    """Task model for queue."""
    id: str
    title: str
    description: str
    priority: str = "medium"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class RateLimitResponse(BaseModel):
    """Rate limit response."""
    allowed: bool
    current_count: int
    limit: int
    window: int
    message: str


class CacheStats(BaseModel):
    """Cache statistics."""
    connected: bool
    total_keys: int
    memory_used: str
    uptime_seconds: int
    operations_per_second: float


# ============================================================================
# API Endpoints - Basic Cache Operations
# ============================================================================

@app.get("/")
async def root():
    """API root with available endpoints."""
    return {
        "message": "Redis Cache Demo API",
        "endpoints": {
            "cache": {
                "GET /cache/{key}": "Get cached value",
                "POST /cache": "Set cache value",
                "DELETE /cache/{key}": "Delete cached value",
                "GET /cache": "List all keys"
            },
            "users": {
                "POST /users": "Create/cache user profile",
                "GET /users/{user_id}": "Get user profile (with caching)",
                "DELETE /users/{user_id}": "Delete user from cache"
            },
            "rate_limit": {
                "GET /rate-limit/check": "Check rate limit (10 req/min)"
            },
            "lock": {
                "POST /lock/{resource}": "Acquire distributed lock and process"
            },
            "queue": {
                "POST /queue/tasks": "Add task to queue",
                "GET /queue/tasks": "Get next task from queue",
                "GET /queue/tasks/all": "View all tasks in queue"
            },
            "stats": {
                "GET /stats": "Get cache statistics"
            }
        }
    }


@app.post("/cache", status_code=201)
async def set_cache(item: CacheItem):
    """
    Set a value in cache.
    
    - **key**: Cache key
    - **value**: Value to cache
    - **ttl**: Time to live in seconds (optional)
    """
    ttl = item.ttl if item.ttl is not None else redis_config.default_ttl
    success = await redis_client.set(item.key, item.value, ttl=ttl)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to set cache")
    
    actual_ttl = await redis_client.ttl(item.key)
    
    return {
        "message": "Cache set successfully",
        "key": item.key,
        "ttl_seconds": actual_ttl
    }


@app.get("/cache/{key}")
async def get_cache(key: str):
    """
    Get a value from cache.
    
    - **key**: Cache key to retrieve
    """
    value = await redis_client.get(key)
    
    if value is None:
        raise HTTPException(status_code=404, detail=f"Key '{key}' not found in cache")
    
    ttl = await redis_client.ttl(key)
    
    return {
        "key": key,
        "value": value,
        "ttl_seconds": ttl if ttl > 0 else None
    }


@app.delete("/cache/{key}")
async def delete_cache(key: str):
    """
    Delete a key from cache.
    
    - **key**: Cache key to delete
    """
    count = await redis_client.delete(key)
    
    if count == 0:
        raise HTTPException(status_code=404, detail=f"Key '{key}' not found")
    
    return {
        "message": "Cache deleted successfully",
        "key": key
    }


@app.get("/cache")
async def list_cache_keys(pattern: str = Query("*", description="Key pattern to match")):
    """
    List all cache keys matching pattern.
    
    - **pattern**: Pattern to match (default: *)
    """
    keys = []
    async for key in redis_client.scan_iter(match=pattern, count=100):
        ttl = await redis_client.ttl(key)
        keys.append({
            "key": key,
            "ttl_seconds": ttl if ttl > 0 else None
        })
    
    return {
        "pattern": pattern,
        "count": len(keys),
        "keys": keys
    }


# ============================================================================
# API Endpoints - User Profile Caching
# ============================================================================

@app.post("/users", status_code=201)
async def create_user(profile: UserProfile):
    """
    Create/update user profile in cache.
    
    Demonstrates hash operations for structured data.
    """
    cache_key = f"user:{profile.user_id}"
    
    # Store as hash for structured access
    await redis_client.hset(cache_key, "name", profile.name)
    await redis_client.hset(cache_key, "email", profile.email)
    
    if profile.age:
        await redis_client.hset(cache_key, "age", profile.age)
    
    if profile.city:
        await redis_client.hset(cache_key, "city", profile.city)
    
    await redis_client.hset(cache_key, "created_at", profile.created_at)
    
    # Set expiration
    await redis_client.expire(cache_key, 3600)  # 1 hour
    
    return {
        "message": "User profile cached successfully",
        "user_id": profile.user_id,
        "cache_key": cache_key,
        "ttl_seconds": 3600
    }


@app.get("/users/{user_id}")
async def get_user(user_id: str):
    """
    Get user profile from cache.
    
    Returns cached user data with cache hit/miss info.
    """
    cache_key = f"user:{user_id}"
    
    # Check if user exists
    exists = await redis_client.exists(cache_key)
    if not exists:
        raise HTTPException(
            status_code=404,
            detail=f"User '{user_id}' not found in cache"
        )
    
    # Get all user data
    user_data = await redis_client.hgetall(cache_key)
    ttl = await redis_client.ttl(cache_key)
    
    return {
        "user_id": user_id,
        "profile": user_data,
        "cache_hit": True,
        "ttl_seconds": ttl
    }


@app.delete("/users/{user_id}")
async def delete_user(user_id: str):
    """Delete user profile from cache."""
    cache_key = f"user:{user_id}"
    count = await redis_client.delete(cache_key)
    
    if count == 0:
        raise HTTPException(
            status_code=404,
            detail=f"User '{user_id}' not found"
        )
    
    return {
        "message": "User deleted from cache",
        "user_id": user_id
    }


# ============================================================================
# API Endpoints - Rate Limiting
# ============================================================================

@app.get("/rate-limit/check", response_model=RateLimitResponse)
async def check_rate_limit(
    user_id: str = Query(..., description="User ID to check rate limit for"),
    limit: int = Query(10, description="Request limit"),
    window: int = Query(60, description="Time window in seconds")
):
    """
    Check rate limit using Lua script.
    
    - **user_id**: User identifier
    - **limit**: Maximum requests allowed (default: 10)
    - **window**: Time window in seconds (default: 60)
    
    Returns whether request is allowed and current count.
    """
    result = await redis_client.execute_script(
        "rate_limit",
        keys=[f"rate_limit:{user_id}"],
        args=[limit, window]
    )
    
    allowed, current_count = result
    
    return RateLimitResponse(
        allowed=bool(allowed),
        current_count=int(current_count),
        limit=limit,
        window=window,
        message="Request allowed" if allowed else f"Rate limit exceeded ({current_count}/{limit})"
    )


# ============================================================================
# API Endpoints - Distributed Locking
# ============================================================================

@app.post("/lock/{resource}")
async def process_with_lock(
    resource: str,
    processing_time: int = Query(2, description="Simulated processing time in seconds")
):
    """
    Process resource with distributed lock.
    
    Demonstrates distributed locking to prevent concurrent access.
    Only one request can process the resource at a time.
    """
    try:
        async with redis_client.lock(
            f"resource:{resource}",
            timeout=10.0,
            blocking_timeout=3.0
        ):
            logger.info(f"Lock acquired for resource: {resource}")
            
            # Simulate processing
            await asyncio.sleep(processing_time)
            
            return {
                "message": "Resource processed successfully",
                "resource": resource,
                "processing_time": processing_time,
                "locked": True
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=409,
            detail=f"Could not acquire lock for resource '{resource}': {str(e)}"
        )


# ============================================================================
# API Endpoints - Task Queue
# ============================================================================

@app.post("/queue/tasks", status_code=201)
async def add_task(task: Task):
    """
    Add task to queue.
    
    Demonstrates list operations for FIFO queue.
    """
    # Push task to queue (FIFO - right push)
    await redis_client.rpush("task_queue", task.dict())
    
    # Get queue length
    queue_tasks = await redis_client.lrange("task_queue", 0, -1)
    
    return {
        "message": "Task added to queue",
        "task_id": task.id,
        "queue_position": len(queue_tasks),
        "queue_length": len(queue_tasks)
    }


@app.get("/queue/tasks")
async def get_next_task():
    """
    Get and remove next task from queue.
    
    Returns the oldest task (FIFO).
    """
    # Pop from left (FIFO)
    task = await redis_client.lpop("task_queue")
    
    if task is None:
        raise HTTPException(status_code=404, detail="No tasks in queue")
    
    # Get remaining queue length
    queue_tasks = await redis_client.lrange("task_queue", 0, -1)
    
    return {
        "task": task,
        "remaining_tasks": len(queue_tasks)
    }


@app.get("/queue/tasks/all")
async def view_all_tasks():
    """
    View all tasks in queue without removing them.
    """
    tasks = await redis_client.lrange("task_queue", 0, -1)
    
    return {
        "queue_length": len(tasks),
        "tasks": tasks
    }


@app.delete("/queue/tasks")
async def clear_queue():
    """Clear all tasks from queue."""
    await redis_client.delete("task_queue")
    
    return {
        "message": "Queue cleared successfully"
    }


# ============================================================================
# API Endpoints - Statistics
# ============================================================================

@app.get("/stats", response_model=CacheStats)
async def get_cache_stats():
    """
    Get Redis cache statistics.
    
    Returns connection status, memory usage, and performance metrics.
    """
    # Check connection
    connected = await redis_client.ping()
    
    # Get Redis info
    info = await redis_client.info()
    
    # Count keys
    key_count = 0
    async for _ in redis_client.scan_iter(match="*", count=1000):
        key_count += 1
    
    return CacheStats(
        connected=connected,
        total_keys=key_count,
        memory_used=info.get("used_memory_human", "N/A"),
        uptime_seconds=info.get("uptime_in_seconds", 0),
        operations_per_second=float(info.get("instantaneous_ops_per_sec", 0))
    )


@app.post("/stats/reset")
async def reset_demo_data():
    """
    Reset all demo data.
    
    ⚠️ Deletes all keys with 'demo_api:' prefix.
    """
    deleted = 0
    async for key in redis_client.scan_iter(match="*", count=100):
        await redis_client.delete(key)
        deleted += 1
    
    return {
        "message": "Demo data reset successfully",
        "keys_deleted": deleted
    }


# ============================================================================
# Run Application
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*70)
    print("🚀 Starting Redis Cache Demo API")
    print("="*70)
    print("\n📚 Interactive API Documentation:")
    print("   Swagger UI: http://localhost:8002/docs")
    print("   ReDoc:      http://localhost:8002/redoc")
    print("\n🔗 Example Endpoints:")
    print("   GET  http://localhost:8002/")
    print("   POST http://localhost:8002/cache")
    print("   GET  http://localhost:8002/cache/mykey")
    print("   POST http://localhost:8002/users")
    print("   GET  http://localhost:8002/rate-limit/check?user_id=user123")
    print("   POST http://localhost:8002/queue/tasks")
    print("   GET  http://localhost:8002/stats")
    print("\n" + "="*70 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )
