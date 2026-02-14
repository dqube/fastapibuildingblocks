"""
Redis Cache Client

Production-ready Redis client with:
- Connection pooling
- Lua script support
- Automatic serialization/deserialization
- TTL management
- Key prefix support
- Distributed locking
- Batch operations
- Pipeline support
- Health checking
"""

import logging
import json
import pickle
from typing import Any, Optional, List, Dict, Union, Callable
from datetime import timedelta
import asyncio
from contextlib import asynccontextmanager

import redis.asyncio as redis
from redis.asyncio import Redis, ConnectionPool
from redis.exceptions import RedisError, ConnectionError, TimeoutError

from .config import RedisConfig

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Production-ready Redis client wrapper.
    
    Features:
    - Async/await support
    - Connection pooling
    - Automatic serialization (JSON/Pickle)
    - Key prefixing
    - TTL management
    - Lua script execution
    - Distributed locking
    - Batch operations
    - Pipeline support
    - Health checking
    """
    
    def __init__(self, config: RedisConfig):
        """
        Initialize Redis client.
        
        Args:
            config: Redis configuration
        """
        self.config = config
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[Redis] = None
        self._scripts: Dict[str, Any] = {}  # Cached Lua scripts
        
    async def connect(self) -> None:
        """Establish connection to Redis."""
        if self._client is not None:
            return
        
        try:
            # Create connection pool
            self._pool = ConnectionPool(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                username=self.config.username,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                socket_keepalive=self.config.socket_keepalive,
                retry_on_timeout=self.config.retry_on_timeout,
                encoding=self.config.encoding,
                decode_responses=self.config.decode_responses,
                health_check_interval=self.config.health_check_interval,
            )
            
            self._client = Redis(connection_pool=self._pool)
            
            # Test connection
            await self._client.ping()
            logger.info(f"Connected to Redis at {self.config.host}:{self.config.port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None
        
        if self._pool:
            await self._pool.disconnect()
            self._pool = None
        
        logger.info("Disconnected from Redis")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    def _make_key(self, key: str) -> str:
        """Apply key prefix if configured."""
        if self.config.key_prefix:
            return f"{self.config.key_prefix}{key}"
        return key
    
    def _serialize(self, value: Any, use_json: bool = True) -> Union[str, bytes]:
        """Serialize value for storage."""
        if isinstance(value, (str, int, float, bool)):
            return str(value)
        
        if use_json:
            try:
                return json.dumps(value)
            except (TypeError, ValueError):
                # Fall back to pickle if JSON fails
                return pickle.dumps(value)
        else:
            return pickle.dumps(value)
    
    def _deserialize(self, value: Union[str, bytes], use_json: bool = True) -> Any:
        """Deserialize value from storage."""
        if value is None:
            return None
        
        if isinstance(value, bytes):
            try:
                return pickle.loads(value)
            except Exception:
                value = value.decode(self.config.encoding)
        
        if use_json:
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        
        return value
    
    # ========================================================================
    # Basic Operations
    # ========================================================================
    
    async def get(self, key: str, default: Any = None, use_json: bool = True) -> Any:
        """
        Get value by key.
        
        Args:
            key: Cache key
            default: Default value if key not found
            use_json: Use JSON serialization (faster, but limited types)
            
        Returns:
            Cached value or default
        """
        try:
            value = await self._client.get(self._make_key(key))
            if value is None:
                return default
            return self._deserialize(value, use_json)
        except RedisError as e:
            logger.error(f"Failed to get key '{key}': {e}")
            return default
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        use_json: bool = True,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """
        Set value for key.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = use default TTL)
            use_json: Use JSON serialization
            nx: Set only if key does not exist
            xx: Set only if key exists
            
        Returns:
            True if successful
        """
        try:
            ttl = ttl if ttl is not None else self.config.default_ttl
            serialized = self._serialize(value, use_json)
            
            result = await self._client.set(
                self._make_key(key),
                serialized,
                ex=ttl if ttl > 0 else None,
                nx=nx,
                xx=xx
            )
            return bool(result)
        except RedisError as e:
            logger.error(f"Failed to set key '{key}': {e}")
            return False
    
    async def delete(self, *keys: str) -> int:
        """
        Delete one or more keys.
        
        Args:
            *keys: Keys to delete
            
        Returns:
            Number of keys deleted
        """
        try:
            prefixed_keys = [self._make_key(k) for k in keys]
            return await self._client.delete(*prefixed_keys)
        except RedisError as e:
            logger.error(f"Failed to delete keys: {e}")
            return 0
    
    async def exists(self, *keys: str) -> int:
        """
        Check if keys exist.
        
        Args:
            *keys: Keys to check
            
        Returns:
            Number of keys that exist
        """
        try:
            prefixed_keys = [self._make_key(k) for k in keys]
            return await self._client.exists(*prefixed_keys)
        except RedisError as e:
            logger.error(f"Failed to check existence of keys: {e}")
            return 0
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time for key."""
        try:
            return await self._client.expire(self._make_key(key), seconds)
        except RedisError as e:
            logger.error(f"Failed to set expiration for key '{key}': {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """Get remaining TTL for key in seconds."""
        try:
            return await self._client.ttl(self._make_key(key))
        except RedisError as e:
            logger.error(f"Failed to get TTL for key '{key}': {e}")
            return -2  # Key doesn't exist
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment value by amount."""
        try:
            return await self._client.incrby(self._make_key(key), amount)
        except RedisError as e:
            logger.error(f"Failed to increment key '{key}': {e}")
            raise
    
    async def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement value by amount."""
        try:
            return await self._client.decrby(self._make_key(key), amount)
        except RedisError as e:
            logger.error(f"Failed to decrement key '{key}': {e}")
            raise
    
    # ========================================================================
    # Hash Operations
    # ========================================================================
    
    async def hget(self, name: str, key: str, use_json: bool = True) -> Any:
        """Get value from hash."""
        try:
            value = await self._client.hget(self._make_key(name), key)
            return self._deserialize(value, use_json)
        except RedisError as e:
            logger.error(f"Failed to get hash field '{name}:{key}': {e}")
            return None
    
    async def hset(
        self,
        name: str,
        key: str,
        value: Any,
        use_json: bool = True
    ) -> int:
        """Set value in hash."""
        try:
            serialized = self._serialize(value, use_json)
            return await self._client.hset(self._make_key(name), key, serialized)
        except RedisError as e:
            logger.error(f"Failed to set hash field '{name}:{key}': {e}")
            return 0
    
    async def hgetall(self, name: str, use_json: bool = True) -> Dict[str, Any]:
        """Get all fields and values from hash."""
        try:
            data = await self._client.hgetall(self._make_key(name))
            return {
                k.decode() if isinstance(k, bytes) else k: 
                self._deserialize(v, use_json)
                for k, v in data.items()
            }
        except RedisError as e:
            logger.error(f"Failed to get all hash fields for '{name}': {e}")
            return {}
    
    async def hdel(self, name: str, *keys: str) -> int:
        """Delete fields from hash."""
        try:
            return await self._client.hdel(self._make_key(name), *keys)
        except RedisError as e:
            logger.error(f"Failed to delete hash fields from '{name}': {e}")
            return 0
    
    # ========================================================================
    # List Operations
    # ========================================================================
    
    async def lpush(self, key: str, *values: Any, use_json: bool = True) -> int:
        """Push values to head of list."""
        try:
            serialized = [self._serialize(v, use_json) for v in values]
            return await self._client.lpush(self._make_key(key), *serialized)
        except RedisError as e:
            logger.error(f"Failed to lpush to '{key}': {e}")
            return 0
    
    async def rpush(self, key: str, *values: Any, use_json: bool = True) -> int:
        """Push values to tail of list."""
        try:
            serialized = [self._serialize(v, use_json) for v in values]
            return await self._client.rpush(self._make_key(key), *serialized)
        except RedisError as e:
            logger.error(f"Failed to rpush to '{key}': {e}")
            return 0
    
    async def lpop(self, key: str, use_json: bool = True) -> Any:
        """Pop value from head of list."""
        try:
            value = await self._client.lpop(self._make_key(key))
            return self._deserialize(value, use_json)
        except RedisError as e:
            logger.error(f"Failed to lpop from '{key}': {e}")
            return None
    
    async def rpop(self, key: str, use_json: bool = True) -> Any:
        """Pop value from tail of list."""
        try:
            value = await self._client.rpop(self._make_key(key))
            return self._deserialize(value, use_json)
        except RedisError as e:
            logger.error(f"Failed to rpop from '{key}': {e}")
            return None
    
    async def lrange(
        self,
        key: str,
        start: int = 0,
        end: int = -1,
        use_json: bool = True
    ) -> List[Any]:
        """Get range of values from list."""
        try:
            values = await self._client.lrange(self._make_key(key), start, end)
            return [self._deserialize(v, use_json) for v in values]
        except RedisError as e:
            logger.error(f"Failed to lrange from '{key}': {e}")
            return []
    
    # ========================================================================
    # Set Operations
    # ========================================================================
    
    async def sadd(self, key: str, *members: Any, use_json: bool = True) -> int:
        """Add members to set."""
        try:
            serialized = [self._serialize(m, use_json) for m in members]
            return await self._client.sadd(self._make_key(key), *serialized)
        except RedisError as e:
            logger.error(f"Failed to sadd to '{key}': {e}")
            return 0
    
    async def srem(self, key: str, *members: Any, use_json: bool = True) -> int:
        """Remove members from set."""
        try:
            serialized = [self._serialize(m, use_json) for m in members]
            return await self._client.srem(self._make_key(key), *serialized)
        except RedisError as e:
            logger.error(f"Failed to srem from '{key}': {e}")
            return 0
    
    async def smembers(self, key: str, use_json: bool = True) -> set:
        """Get all members of set."""
        try:
            values = await self._client.smembers(self._make_key(key))
            return {self._deserialize(v, use_json) for v in values}
        except RedisError as e:
            logger.error(f"Failed to smembers from '{key}': {e}")
            return set()
    
    async def sismember(self, key: str, member: Any, use_json: bool = True) -> bool:
        """Check if member is in set."""
        try:
            serialized = self._serialize(member, use_json)
            return await self._client.sismember(self._make_key(key), serialized)
        except RedisError as e:
            logger.error(f"Failed to check sismember in '{key}': {e}")
            return False
    
    # ========================================================================
    # Lua Script Support
    # ========================================================================
    
    def register_script(self, name: str, script: str) -> None:
        """
        Register a Lua script for later execution.
        
        Args:
            name: Unique name for the script
            script: Lua script code
        """
        self._scripts[name] = self._client.register_script(script)
        logger.info(f"Registered Lua script: {name}")
    
    async def execute_script(
        self,
        name: str,
        keys: List[str] = None,
        args: List[Any] = None
    ) -> Any:
        """
        Execute a registered Lua script.
        
        Args:
            name: Name of registered script
            keys: Redis keys to pass to script (will be prefixed)
            args: Additional arguments to pass to script
            
        Returns:
            Script execution result
        """
        if name not in self._scripts:
            raise ValueError(f"Script '{name}' not registered")
        
        try:
            # Apply key prefix to all keys
            prefixed_keys = [self._make_key(k) for k in (keys or [])]
            result = await self._scripts[name](keys=prefixed_keys, args=args or [])
            return result
        except RedisError as e:
            logger.error(f"Failed to execute script '{name}': {e}")
            raise
    
    async def eval(
        self,
        script: str,
        keys: List[str] = None,
        args: List[Any] = None
    ) -> Any:
        """
        Execute Lua script directly (without registration).
        
        Args:
            script: Lua script code
            keys: Redis keys to pass to script
            args: Additional arguments to pass to script
            
        Returns:
            Script execution result
        """
        try:
            prefixed_keys = [self._make_key(k) for k in (keys or [])]
            return await self._client.eval(script, len(prefixed_keys), *prefixed_keys, *(args or []))
        except RedisError as e:
            logger.error(f"Failed to execute Lua script: {e}")
            raise
    
    # ========================================================================
    # Distributed Lock
    # ========================================================================
    
    @asynccontextmanager
    async def lock(
        self,
        name: str,
        timeout: float = 10.0,
        blocking_timeout: float = 5.0
    ):
        """
        Distributed lock context manager.
        
        Args:
            name: Lock name
            timeout: Lock timeout in seconds
            blocking_timeout: How long to wait to acquire lock
            
        Example:
            async with client.lock("my-resource"):
                # Critical section
                pass
        """
        lock = self._client.lock(
            self._make_key(f"lock:{name}"),
            timeout=timeout,
            blocking_timeout=blocking_timeout
        )
        
        try:
            await lock.acquire()
            logger.debug(f"Acquired lock: {name}")
            yield lock
        finally:
            try:
                await lock.release()
                logger.debug(f"Released lock: {name}")
            except Exception as e:
                logger.warning(f"Failed to release lock '{name}': {e}")
    
    # ========================================================================
    # Pipeline Support
    # ========================================================================
    
    @asynccontextmanager
    async def pipeline(self, transaction: bool = True):
        """
        Pipeline context manager for batching commands.
        
        Args:
            transaction: Use MULTI/EXEC transaction
            
        Example:
            async with client.pipeline() as pipe:
                await pipe.set("key1", "value1")
                await pipe.set("key2", "value2")
                results = await pipe.execute()
        """
        pipe = self._client.pipeline(transaction=transaction)
        try:
            yield pipe
        finally:
            pass
    
    # ========================================================================
    # Health & Maintenance
    # ========================================================================
    
    async def ping(self) -> bool:
        """Check if Redis is responding."""
        try:
            result = await self._client.ping()
            return result
        except RedisError as e:
            logger.error(f"Redis ping failed: {e}")
            return False
    
    async def info(self, section: Optional[str] = None) -> Dict[str, Any]:
        """Get Redis server information."""
        try:
            return await self._client.info(section)
        except RedisError as e:
            logger.error(f"Failed to get Redis info: {e}")
            return {}
    
    async def flushdb(self) -> bool:
        """Flush current database (USE WITH CAUTION)."""
        try:
            await self._client.flushdb()
            logger.warning("Flushed Redis database")
            return True
        except RedisError as e:
            logger.error(f"Failed to flush database: {e}")
            return False
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """
        Get keys matching pattern.
        
        WARNING: Use with caution in production (use SCAN instead for large datasets).
        """
        try:
            prefixed_pattern = self._make_key(pattern)
            keys = await self._client.keys(prefixed_pattern)
            
            # Remove prefix from returned keys
            if self.config.key_prefix:
                prefix_len = len(self.config.key_prefix)
                return [k[prefix_len:] if k.startswith(self.config.key_prefix) else k for k in keys]
            
            return keys
        except RedisError as e:
            logger.error(f"Failed to get keys: {e}")
            return []
    
    async def scan_iter(self, match: str = "*", count: int = 100):
        """
        Iterate over keys matching pattern (better than keys() for large datasets).
        
        Args:
            match: Key pattern
            count: Number of keys to return per iteration
            
        Yields:
            Matching keys
        """
        prefixed_match = self._make_key(match)
        
        async for key in self._client.scan_iter(match=prefixed_match, count=count):
            # Remove prefix from returned keys
            if self.config.key_prefix and key.startswith(self.config.key_prefix):
                yield key[len(self.config.key_prefix):]
            else:
                yield key
    
    # ========================================================================
    # Cache Decorators
    # ========================================================================
    
    def cached(
        self,
        key_template: str,
        ttl: Optional[int] = None,
        use_json: bool = True
    ):
        """
        Decorator to cache function results.
        
        Args:
            key_template: Cache key template (can use {arg_name} placeholders)
            ttl: Cache TTL in seconds
            use_json: Use JSON serialization
            
        Example:
            @redis_client.cached("user:{user_id}", ttl=300)
            async def get_user(user_id: int):
                return await fetch_user_from_db(user_id)
        """
        def decorator(func: Callable):
            async def wrapper(*args, **kwargs):
                # Build cache key from template
                import inspect
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                
                cache_key = key_template.format(**bound_args.arguments)
                
                # Try to get from cache
                cached_value = await self.get(cache_key, use_json=use_json)
                if cached_value is not None:
                    logger.debug(f"Cache hit: {cache_key}")
                    return cached_value
                
                # Execute function
                logger.debug(f"Cache miss: {cache_key}")
                result = await func(*args, **kwargs)
                
                # Cache result
                await self.set(cache_key, result, ttl=ttl, use_json=use_json)
                
                return result
            
            return wrapper
        return decorator
