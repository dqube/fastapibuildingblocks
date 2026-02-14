"""
Redis Cache Demo

Demonstrates Redis caching capabilities including:
1. Basic cache operations (get/set/delete)
2. Hash, List, and Set operations
3. Lua script execution
4. Distributed locking
5. Pipeline operations
6. Cache decorator
7. Integration with External API configuration
"""

import asyncio
import logging
from datetime import datetime

from building_blocks.infrastructure.cache import RedisClient, RedisConfig, ExternalApiConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_basic_operations():
    """Demo 1: Basic cache operations."""
    print("\n" + "="*70)
    print("Demo 1: Basic Cache Operations")
    print("="*70)
    
    config = RedisConfig(
        host="localhost",
        port=6379,
        key_prefix="demo:",
        default_ttl=300
    )
    
    async with RedisClient(config) as client:
        # Set and get
        await client.set("user:1", {"id": 1, "name": "John Doe", "email": "john@example.com"})
        user = await client.get("user:1")
        print(f"✓ Retrieved user: {user}")
        
        # Set with custom TTL
        await client.set("session:abc123", {"user_id": 1, "expires": "2026-02-15"}, ttl=60)
        print(f"✓ Set session with 60s TTL")
        
        # Check TTL
        ttl = await client.ttl("session:abc123")
        print(f"✓ Session TTL: {ttl} seconds remaining")
        
        # Increment/Decrement
        await client.set("counter", 0)
        await client.increment("counter", 5)
        await client.increment("counter", 3)
        counter = await client.get("counter")
        print(f"✓ Counter after increments: {counter}")
        
        # Check existence
        exists = await client.exists("user:1", "user:999")
        print(f"✓ Keys exist: {exists}/2")


async def demo_hash_operations():
    """Demo 2: Hash operations for structured data."""
    print("\n" + "="*70)
    print("Demo 2: Hash Operations")
    print("="*70)
    
    config = RedisConfig(host="localhost", port=6379, key_prefix="demo:")
    
    async with RedisClient(config) as client:
        # Store user profile in hash
        await client.hset("profile:1", "name", "Alice Smith")
        await client.hset("profile:1", "email", "alice@example.com")
        await client.hset("profile:1", "age", 30)
        await client.hset("profile:1", "city", "San Francisco")
        
        # Get single field
        name = await client.hget("profile:1", "name")
        print(f"✓ User name: {name}")
        
        # Get all fields
        profile = await client.hgetall("profile:1")
        print(f"✓ Full profile: {profile}")
        
        # Delete field
        await client.hdel("profile:1", "age")
        print(f"✓ Deleted 'age' field from profile")


async def demo_list_operations():
    """Demo 3: List operations for queues."""
    print("\n" + "="*70)
    print("Demo 3: List Operations (Queues)")
    print("="*70)
    
    config = RedisConfig(host="localhost", port=6379, key_prefix="demo:")
    
    async with RedisClient(config) as client:
        # Task queue
        await client.rpush("tasks", 
            {"id": 1, "task": "Send email", "priority": "high"},
            {"id": 2, "task": "Update database", "priority": "medium"},
            {"id": 3, "task": "Generate report", "priority": "low"}
        )
        print(f"✓ Pushed 3 tasks to queue")
        
        # Process tasks (FIFO)
        task1 = await client.lpop("tasks")
        print(f"✓ Processing task: {task1}")
        
        # View remaining tasks
        remaining = await client.lrange("tasks", 0, -1)
        print(f"✓ Remaining tasks: {len(remaining)}")
        for task in remaining:
            print(f"  - {task}")


async def demo_set_operations():
    """Demo 4: Set operations for unique collections."""
    print("\n" + "="*70)
    print("Demo 4: Set Operations")
    print("="*70)
    
    config = RedisConfig(host="localhost", port=6379, key_prefix="demo:")
    
    async with RedisClient(config) as client:
        # Active users set
        await client.sadd("active_users", "user1", "user2", "user3", "user2")  # user2 duplicate
        
        members = await client.smembers("active_users")
        print(f"✓ Active users (unique): {members}")
        
        # Check membership
        is_active = await client.sismember("active_users", "user1")
        print(f"✓ Is user1 active? {is_active}")
        
        # Remove user
        await client.srem("active_users", "user3")
        print(f"✓ Removed user3 from active users")


async def demo_lua_scripts():
    """Demo 5: Lua script execution."""
    print("\n" + "="*70)
    print("Demo 5: Lua Script Execution")
    print("="*70)
    
    config = RedisConfig(host="localhost", port=6379, key_prefix="demo:")
    
    async with RedisClient(config) as client:
        # Example 1: Atomic rate limiting script
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
        
        client.register_script("rate_limit", rate_limit_script)
        
        # Test rate limiting (5 requests per 60 seconds)
        for i in range(7):
            allowed = await client.execute_script(
                "rate_limit",
                keys=["rate:api:user123"],
                args=[5, 60]  # limit=5, window=60s
            )
            status = "✓ Allowed" if allowed else "✗ Rate limited"
            print(f"Request {i+1}: {status}")
        
        print("\n" + "-"*70)
        
        # Example 2: Atomic counter with metadata
        counter_script = """
        local key = KEYS[1]
        local amount = tonumber(ARGV[1])
        
        local new_value = redis.call('INCRBY', key, amount)
        local ttl = redis.call('TTL', key)
        
        return {new_value, ttl}
        """
        
        await client.set("visit_count", 100, ttl=3600)
        result = await client.eval(
            counter_script,
            keys=["visit_count"],
            args=[10]
        )
        print(f"\n✓ Counter incremented: new_value={result[0]}, ttl={result[1]}s")
        
        print("\n" + "-"*70)
        
        # Example 3: Atomic check-and-set pattern
        check_and_set_script = """
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
        
        await client.set("inventory:item123", "10")
        
        # Simulate concurrent operations
        success = await client.eval(
            check_and_set_script,
            keys=["inventory:item123"],
            args=["10", "9"]  # expected=10, new=9
        )
        print(f"\n✓ Check-and-set: {'Success' if success else 'Failed'}")


async def demo_distributed_lock():
    """Demo 6: Distributed locking."""
    print("\n" + "="*70)
    print("Demo 6: Distributed Locking")
    print("="*70)
    
    config = RedisConfig(host="localhost", port=6379, key_prefix="demo:")
    
    async with RedisClient(config) as client:
        print("✓ Attempting to acquire lock 'order-processing'...")
        
        async with client.lock("order-processing", timeout=10.0, blocking_timeout=5.0):
            print("✓ Lock acquired! Processing order...")
            await asyncio.sleep(2)  # Simulate work
            print("✓ Order processed!")
        
        print("✓ Lock released automatically")
        
        # Simulate concurrent lock attempts
        async def worker(worker_id: int):
            try:
                async with client.lock("shared-resource", timeout=3.0, blocking_timeout=1.0):
                    print(f"  Worker {worker_id}: Acquired lock")
                    await asyncio.sleep(1)
                    print(f"  Worker {worker_id}: Released lock")
            except Exception as e:
                print(f"  Worker {worker_id}: Failed to acquire lock - {e}")
        
        print("\n✓ Running 3 concurrent workers...")
        await asyncio.gather(
            worker(1),
            worker(2),
            worker(3)
        )


async def demo_pipeline():
    """Demo 7: Pipeline for batch operations."""
    print("\n" + "="*70)
    print("Demo 7: Pipeline Operations")
    print("="*70)
    
    config = RedisConfig(host="localhost", port=6379, key_prefix="demo:")
    
    async with RedisClient(config) as client:
        # Batch operations in pipeline
        async with client.pipeline() as pipe:
            pipe.set("metric:cpu", 45.5)
            pipe.set("metric:memory", 78.2)
            pipe.set("metric:disk", 23.1)
            pipe.set("metric:network", 12.8)
            results = await pipe.execute()
        
        print(f"✓ Executed {len(results)} operations in pipeline")
        
        # Transaction pipeline
        async with client.pipeline(transaction=True) as pipe:
            pipe.get("metric:cpu")
            pipe.get("metric:memory")
            pipe.get("metric:disk")
            metrics = await pipe.execute()
        
        print(f"✓ Retrieved metrics: CPU={metrics[0]}, Memory={metrics[1]}, Disk={metrics[2]}")


async def demo_cache_decorator():
    """Demo 8: Cache decorator for functions."""
    print("\n" + "="*70)
    print("Demo 8: Cache Decorator")
    print("="*70)
    
    config = RedisConfig(host="localhost", port=6379, key_prefix="demo:")
    client = await RedisClient(config).__aenter__()
    
    # Simulate expensive database query
    @client.cached("user:profile:{user_id}", ttl=300)
    async def get_user_profile(user_id: int):
        print(f"  → Fetching user {user_id} from database (expensive)...")
        await asyncio.sleep(1)  # Simulate DB query
        return {
            "id": user_id,
            "name": f"User {user_id}",
            "created_at": datetime.now().isoformat()
        }
    
    print("✓ First call (cache miss):")
    profile1 = await get_user_profile(user_id=42)
    print(f"  Profile: {profile1}")
    
    print("\n✓ Second call (cache hit):")
    profile2 = await get_user_profile(user_id=42)
    print(f"  Profile: {profile2}")
    
    print("\n✓ Third call with different ID (cache miss):")
    profile3 = await get_user_profile(user_id=99)
    print(f"  Profile: {profile3}")
    
    await client.disconnect()


async def demo_external_api_config():
    """Demo 9: External API configuration."""
    print("\n" + "="*70)
    print("Demo 9: External API Configuration")
    print("="*70)
    
    # Example: Payment gateway API configuration
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
    
    print(f"✓ API Name: {payment_api.name}")
    print(f"✓ Base URL: {payment_api.base_url}")
    print(f"✓ Auth Type: {payment_api.auth_type}")
    print(f"✓ Cache Key Prefix: {payment_api.get_cache_key_prefix()}")
    print(f"✓ Circuit Breaker: {'Enabled' if payment_api.enable_circuit_breaker else 'Disabled'}")
    
    print("\n" + "-"*70)
    
    # Example: Third-party OAuth2 API
    oauth_api = ExternalApiConfig(
        name="google-calendar",
        base_url="https://www.googleapis.com/calendar/v3",
        auth_type="oauth2",
        oauth2_token_url="https://oauth2.googleapis.com/token",
        oauth2_client_id="your-client-id",
        oauth2_client_secret="your-client-secret",
        oauth2_scope="https://www.googleapis.com/auth/calendar.readonly",
        enable_caching=True,
        cache_ttl=600,
        rate_limit_enabled=True,
        rate_limit_requests=100,
        rate_limit_period=60
    )
    
    print(f"\n✓ API Name: {oauth_api.name}")
    print(f"✓ Auth Type: {oauth_api.auth_type}")
    print(f"✓ Rate Limit: {oauth_api.rate_limit_requests} requests per {oauth_api.rate_limit_period}s")
    
    print("\n" + "-"*70)
    
    # Example: API with custom headers
    custom_api = ExternalApiConfig(
        name="internal-service",
        base_url="http://internal-api:8000",
        auth_type="custom",
        custom_headers={
            "X-Internal-Auth": "secret-key",
            "X-Service-Name": "user-service",
            "X-Environment": "production"
        },
        enable_caching=False,
        enable_circuit_breaker=True
    )
    
    print(f"\n✓ API Name: {custom_api.name}")
    print(f"✓ Custom Headers: {len(custom_api.custom_headers)} headers")
    for key, value in custom_api.custom_headers.items():
        print(f"  - {key}: {value}")


async def demo_redis_with_api_caching():
    """Demo 10: Using Redis for API response caching."""
    print("\n" + "="*70)
    print("Demo 10: Redis + External API Caching Pattern")
    print("="*70)
    
    # Setup Redis
    redis_config = RedisConfig(
        host="localhost",
        port=6379,
        key_prefix="api_cache:",
        default_ttl=300
    )
    
    # Setup external API config
    api_config = ExternalApiConfig(
        name="weather-api",
        base_url="https://api.weather.com/v1",
        auth_type="api_key",
        api_key="your-api-key",
        api_key_header="X-API-Key",
        enable_caching=True,
        cache_ttl=600
    )
    
    async with RedisClient(redis_config) as cache:
        # Simulate API call with caching
        async def fetch_weather(city: str):
            cache_key = f"{api_config.get_cache_key_prefix()}weather:{city}"
            
            # Check cache first
            cached = await cache.get(cache_key)
            if cached:
                print(f"  ✓ Cache HIT for {city}")
                return cached
            
            print(f"  → Cache MISS for {city}, fetching from API...")
            await asyncio.sleep(1)  # Simulate API call
            
            weather_data = {
                "city": city,
                "temperature": 72,
                "condition": "Sunny",
                "timestamp": datetime.now().isoformat()
            }
            
            # Store in cache
            await cache.set(cache_key, weather_data, ttl=api_config.cache_ttl)
            return weather_data
        
        # First call - cache miss
        print("\n✓ First request for San Francisco:")
        weather1 = await fetch_weather("San Francisco")
        print(f"  Result: {weather1['temperature']}°F, {weather1['condition']}")
        
        # Second call - cache hit
        print("\n✓ Second request for San Francisco:")
        weather2 = await fetch_weather("San Francisco")
        print(f"  Result: {weather2['temperature']}°F, {weather2['condition']}")
        
        # Different city - cache miss
        print("\n✓ Request for New York:")
        weather3 = await fetch_weather("New York")
        print(f"  Result: {weather3['temperature']}°F, {weather3['condition']}")


async def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("REDIS CACHE DEMONSTRATION")
    print("Features: Basic ops, Hashes, Lists, Sets, Lua scripts, Locks, Pipelines")
    print("="*70)
    
    try:
        await demo_basic_operations()
        await demo_hash_operations()
        await demo_list_operations()
        await demo_set_operations()
        await demo_lua_scripts()
        await demo_distributed_lock()
        await demo_pipeline()
        await demo_cache_decorator()
        await demo_external_api_config()
        await demo_redis_with_api_caching()
        
        print("\n" + "="*70)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
