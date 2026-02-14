"""
Redis Cache Testing API Endpoints

Provides endpoints to test Redis caching capabilities including:
- Basic cache operations
- Hash operations (structured data)
- List operations (queues)
- Set operations (unique collections)
- Lua script execution
- Distributed locking
- Cache statistics
"""

from typing import Any, List, Optional, Dict
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import asyncio
from datetime import datetime

from building_blocks.infrastructure.cache import RedisClient, RedisConfig

# Create router
router = APIRouter()

# Initialize Redis client
redis_config = RedisConfig(
    host="redis",  # Docker service name
    port=6379,
    key_prefix="app:",
    default_ttl=3600,
    max_connections=20
)
redis_client = RedisClient(redis_config)


# ==================== Pydantic Models ====================

class CacheItem(BaseModel):
    """Cache item model."""
    key: str = Field(..., description="Cache key")
    value: Any = Field(..., description="Cache value (any JSON serializable data)")
    ttl: Optional[int] = Field(None, description="Time to live in seconds")


class CacheResponse(BaseModel):
    """Cache operation response."""
    success: bool
    message: str
    data: Optional[Any] = None


class UserProfile(BaseModel):
    """User profile model for hash operations."""
    user_id: str = Field(..., description="User ID")
    name: str = Field(..., description="User name")
    email: str = Field(..., description="User email")
    age: Optional[int] = Field(None, description="User age")
    city: Optional[str] = Field(None, description="User city")


class Task(BaseModel):
    """Task model for queue operations."""
    id: str
    title: str
    description: Optional[str] = None
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class RateLimitRequest(BaseModel):
    """Rate limit check request."""
    user_id: str
    limit: int = Field(default=10, ge=1, le=1000)
    window: int = Field(default=60, ge=1, le=3600)


class CacheStats(BaseModel):
    """Cache statistics."""
    connected: bool
    total_keys: int
    memory_used: Optional[str] = None
    uptime_seconds: Optional[int] = None
    ops_per_second: Optional[int] = None


# ==================== Startup/Shutdown ====================

@router.on_event("startup")
async def startup_redis():
    """Connect to Redis on startup."""
    try:
        await redis_client.connect()
        
        # Register Lua scripts
        rate_limit_script = """
        local key = KEYS[1]
        local limit = tonumber(ARGV[1])
        local window = tonumber(ARGV[2])
        
        local current = redis.call('GET', key)
        if not current then
            redis.call('SETEX', key, window, 1)
            return {1, limit - 1}
        end
        
        current = tonumber(current)
        if current < limit then
            redis.call('INCR', key)
            return {current + 1, limit - current - 1}
        end
        
        local ttl = redis.call('TTL', key)
        return {current, 0, ttl}
        """
        redis_client.register_script("rate_limit", rate_limit_script)
        
        print("✅ Redis client connected and Lua scripts registered")
    except Exception as e:
        print(f"⚠️  Redis connection failed: {e}")


@router.on_event("shutdown")
async def shutdown_redis():
    """Disconnect from Redis on shutdown."""
    try:
        await redis_client.disconnect()
        print("✅ Redis client disconnected")
    except Exception as e:
        print(f"⚠️  Redis disconnect error: {e}")


# ==================== Basic Cache Operations ====================

@router.post("/cache", response_model=CacheResponse, status_code=status.HTTP_201_CREATED)
async def set_cache(item: CacheItem):
    """
    Set a cache value with optional TTL.
    
    - **key**: Cache key
    - **value**: Any JSON serializable value
    - **ttl**: Time to live in seconds (optional)
    """
    try:
        await redis_client.set(item.key, item.value, ttl=item.ttl)
        ttl_info = f" with {item.ttl}s TTL" if item.ttl else ""
        return CacheResponse(
            success=True,
            message=f"Cache set successfully{ttl_info}",
            data={"key": item.key, "ttl": item.ttl}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set cache: {str(e)}"
        )


@router.get("/cache/{key}", response_model=CacheResponse)
async def get_cache(key: str):
    """
    Get a cache value by key.
    
    - **key**: Cache key to retrieve
    """
    try:
        value = await redis_client.get(key)
        if value is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Key '{key}' not found in cache"
            )
        
        # Get TTL
        ttl = await redis_client.ttl(key)
        
        return CacheResponse(
            success=True,
            message="Cache retrieved successfully",
            data={"key": key, "value": value, "ttl_seconds": ttl}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache: {str(e)}"
        )


@router.delete("/cache/{key}", response_model=CacheResponse)
async def delete_cache(key: str):
    """
    Delete a cache value by key.
    
    - **key**: Cache key to delete
    """
    try:
        deleted = await redis_client.delete(key)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Key '{key}' not found"
            )
        return CacheResponse(
            success=True,
            message="Cache deleted successfully",
            data={"key": key}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete cache: {str(e)}"
        )


@router.get("/cache", response_model=CacheResponse)
async def list_cache_keys(pattern: str = "*", limit: int = 100):
    """
    List cache keys matching a pattern.
    
    - **pattern**: Key pattern (default: *)
    - **limit**: Maximum number of keys to return
    """
    try:
        keys = []
        async for key in redis_client.scan_iter(match=pattern):
            keys.append(key)
            if len(keys) >= limit:
                break
        
        return CacheResponse(
            success=True,
            message=f"Found {len(keys)} keys",
            data={"keys": keys, "total": len(keys)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list keys: {str(e)}"
        )


# ==================== Hash Operations (User Profiles) ====================

@router.post("/users", response_model=CacheResponse, status_code=status.HTTP_201_CREATED)
async def create_user_profile(profile: UserProfile):
    """
    Create a user profile using Redis hashes.
    
    Demonstrates structured data storage with field-level access.
    """
    try:
        key = f"user:{profile.user_id}"
        
        # Store as hash
        await redis_client.hset(key, "user_id", profile.user_id)
        await redis_client.hset(key, "name", profile.name)
        await redis_client.hset(key, "email", profile.email)
        if profile.age:
            await redis_client.hset(key, "age", profile.age)
        if profile.city:
            await redis_client.hset(key, "city", profile.city)
        
        # Set expiration
        await redis_client.expire(key, 3600)
        
        return CacheResponse(
            success=True,
            message="User profile created successfully",
            data={"user_id": profile.user_id, "key": key}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user profile: {str(e)}"
        )


@router.get("/users/{user_id}", response_model=CacheResponse)
async def get_user_profile(user_id: str):
    """
    Get a user profile by ID.
    
    Retrieves all fields from the hash.
    """
    try:
        key = f"user:{user_id}"
        profile = await redis_client.hgetall(key)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User profile '{user_id}' not found"
            )
        
        ttl = await redis_client.ttl(key)
        
        return CacheResponse(
            success=True,
            message="User profile retrieved successfully",
            data={"user_id": user_id, "profile": profile, "ttl_seconds": ttl}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user profile: {str(e)}"
        )


@router.delete("/users/{user_id}", response_model=CacheResponse)
async def delete_user_profile(user_id: str):
    """Delete a user profile."""
    try:
        key = f"user:{user_id}"
        deleted = await redis_client.delete(key)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User profile '{user_id}' not found"
            )
        
        return CacheResponse(
            success=True,
            message="User profile deleted successfully",
            data={"user_id": user_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user profile: {str(e)}"
        )


# ==================== Rate Limiting (Lua Script) ====================

@router.post("/rate-limit/check", response_model=CacheResponse)
async def check_rate_limit(request: RateLimitRequest):
    """
    Check rate limit using Lua script.
    
    Demonstrates atomic operations with Lua scripts.
    - Atomically increments counter and sets TTL
    - Returns current count and remaining requests
    """
    try:
        result = await redis_client.execute_script(
            "rate_limit",
            keys=[f"rate_limit:{request.user_id}"],
            args=[request.limit, request.window]
        )
        
        current_count = result[0]
        remaining = result[1]
        allowed = current_count <= request.limit
        
        response_data = {
            "user_id": request.user_id,
            "allowed": allowed,
            "current_count": current_count,
            "limit": request.limit,
            "remaining": remaining if allowed else 0,
            "window_seconds": request.window
        }
        
        if len(result) > 2:
            response_data["retry_after_seconds"] = result[2]
        
        return CacheResponse(
            success=True,
            message="Rate limit checked" if allowed else "Rate limit exceeded",
            data=response_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check rate limit: {str(e)}"
        )


# ==================== Distributed Locking ====================

@router.post("/lock/{resource}", response_model=CacheResponse)
async def acquire_lock_and_process(resource: str, processing_time: float = 2.0):
    """
    Acquire distributed lock and simulate processing.
    
    Demonstrates cross-process synchronization.
    Only one request can hold the lock at a time.
    """
    try:
        async with redis_client.lock(resource, timeout=10.0, blocking_timeout=3.0):
            # Simulate work
            await asyncio.sleep(processing_time)
            
            return CacheResponse(
                success=True,
                message=f"Lock acquired and processing completed for '{resource}'",
                data={
                    "resource": resource,
                    "processing_time": processing_time,
                    "lock_timeout": 10.0
                }
            )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Could not acquire lock for '{resource}' - resource is busy"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lock operation failed: {str(e)}"
        )


# ==================== Task Queue (List Operations) ====================

@router.post("/queue/tasks", response_model=CacheResponse, status_code=status.HTTP_201_CREATED)
async def add_task(task: Task):
    """
    Add a task to the queue (FIFO).
    
    Demonstrates list operations for queue management.
    """
    try:
        queue_key = "queue:tasks"
        await redis_client.rpush(queue_key, task.dict())
        
        # Get queue length
        queue_length = len(await redis_client.lrange(queue_key, 0, -1))
        
        return CacheResponse(
            success=True,
            message="Task added to queue",
            data={
                "task_id": task.id,
                "queue_position": queue_length,
                "queue_length": queue_length
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add task: {str(e)}"
        )


@router.get("/queue/tasks", response_model=CacheResponse)
async def get_next_task():
    """
    Get and remove the next task from the queue (FIFO).
    
    Returns the oldest task in the queue.
    """
    try:
        queue_key = "queue:tasks"
        task = await redis_client.lpop(queue_key)
        
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No tasks in queue"
            )
        
        # Get remaining queue length
        queue_length = len(await redis_client.lrange(queue_key, 0, -1))
        
        return CacheResponse(
            success=True,
            message="Task retrieved from queue",
            data={
                "task": task,
                "remaining_tasks": queue_length
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task: {str(e)}"
        )


@router.get("/queue/tasks/all", response_model=CacheResponse)
async def view_all_tasks():
    """
    View all tasks in the queue without removing them.
    """
    try:
        queue_key = "queue:tasks"
        tasks = await redis_client.lrange(queue_key, 0, -1)
        
        return CacheResponse(
            success=True,
            message=f"Retrieved {len(tasks)} tasks",
            data={
                "tasks": tasks,
                "total": len(tasks)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to view tasks: {str(e)}"
        )


@router.delete("/queue/tasks", response_model=CacheResponse)
async def clear_task_queue():
    """Clear all tasks from the queue."""
    try:
        queue_key = "queue:tasks"
        deleted = await redis_client.delete(queue_key)
        
        return CacheResponse(
            success=True,
            message="Task queue cleared",
            data={"deleted": deleted > 0}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear queue: {str(e)}"
        )


# ==================== Cache Statistics ====================

@router.get("/stats", response_model=CacheStats)
async def get_cache_stats():
    """
    Get Redis cache statistics.
    
    Returns connection status, key count, memory usage, and performance metrics.
    """
    try:
        # Check connection
        connected = await redis_client.ping()
        
        # Count keys
        keys = []
        async for key in redis_client.scan_iter(match="*"):
            keys.append(key)
        
        # Get Redis info
        info = await redis_client.info()
        
        return CacheStats(
            connected=connected,
            total_keys=len(keys),
            memory_used=info.get("used_memory_human"),
            uptime_seconds=info.get("uptime_in_seconds"),
            ops_per_second=info.get("instantaneous_ops_per_sec")
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


@router.post("/stats/reset", response_model=CacheResponse)
async def reset_demo_data():
    """
    Clear all demo data (keys with 'app:' prefix).
    
    ⚠️ Use with caution - deletes all application keys!
    """
    try:
        deleted_count = 0
        async for key in redis_client.scan_iter(match="*"):
            await redis_client.delete(key)
            deleted_count += 1
        
        return CacheResponse(
            success=True,
            message=f"Reset complete - deleted {deleted_count} keys",
            data={"deleted_keys": deleted_count}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset data: {str(e)}"
        )


# ==================== Health Check ====================

@router.get("/health", response_model=CacheResponse)
async def redis_health():
    """Check Redis connection health."""
    try:
        connected = await redis_client.ping()
        return CacheResponse(
            success=True,
            message="Redis is healthy" if connected else "Redis is not responding",
            data={"connected": connected}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis health check failed: {str(e)}"
        )
