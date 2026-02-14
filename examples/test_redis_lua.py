"""Quick test of Redis Lua script support."""
import asyncio
from building_blocks.infrastructure.cache import RedisClient, RedisConfig

async def test_lua_script():
    config = RedisConfig(host='localhost', port=6379, key_prefix='test:')
    
    async with RedisClient(config) as cache:
        # Rate limiting script
        script = """
        local key = KEYS[1]
        local limit = tonumber(ARGV[1])
        local current = redis.call('GET', key)
        if current and tonumber(current) >= limit then
            return 0
        else
            redis.call('INCR', key)
            if not current then
                redis.call('EXPIRE', key, 60)
            end
            return 1
        end
        """
        
        cache.register_script('rate_limit', script)
        
        print("Testing Lua script rate limiting (3 request limit):")
        # Test rate limiting (3 request limit)
        for i in range(5):
            allowed = await cache.execute_script(
                'rate_limit',
                keys=['rate:test'],
                args=[3]
            )
            status = '✅ Allowed' if allowed else '⛔ Rate limited'
            print(f'  Request {i+1}: {status}')
        
        # Clean up
        await cache.delete('rate:test')
        print("\n✅ Lua script test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_lua_script())
