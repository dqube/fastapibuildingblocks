"""
Example Application Configuration

Demonstrates how to integrate:
- Redis caching configuration
- External API configurations
- Application settings using Pydantic Settings
"""

from typing import List, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from building_blocks.infrastructure.cache import RedisConfig, ExternalApiConfig


class Settings(BaseSettings):
    """
    Application settings with Redis and External API configuration.
    
    Environment variables can be set in .env file or exported:
    - REDIS_HOST=localhost
    - REDIS_PORT=6379
    - PAYMENT_API_TOKEN=sk_test_123...
    """
    
    # ========================================================================
    # Application Settings
    # ========================================================================
    APP_NAME: str = "FastAPI Building Blocks Demo"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
    ]
    
    # ========================================================================
    # Database Settings
    # ========================================================================
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/myapp"
    
    # ========================================================================
    # Redis Cache Settings
    # ========================================================================
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None
    REDIS_USERNAME: str | None = None
    REDIS_KEY_PREFIX: str = "myapp:"
    REDIS_DEFAULT_TTL: int = 3600  # 1 hour
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_SSL_ENABLED: bool = False
    
    # ========================================================================
    # External API: Payment Gateway (Stripe)
    # ========================================================================
    PAYMENT_API_ENABLED: bool = True
    PAYMENT_API_BASE_URL: str = "https://api.stripe.com/v1"
    PAYMENT_API_TOKEN: str = "sk_test_your_token_here"
    PAYMENT_API_TIMEOUT: float = 30.0
    PAYMENT_API_MAX_RETRIES: int = 3
    PAYMENT_API_CACHE_ENABLED: bool = True
    PAYMENT_API_CACHE_TTL: int = 300  # 5 minutes
    
    # ========================================================================
    # External API: SMS Service (Twilio)
    # ========================================================================
    SMS_API_ENABLED: bool = True
    SMS_API_BASE_URL: str = "https://api.twilio.com/2010-04-01"
    SMS_API_ACCOUNT_SID: str = "your_account_sid"
    SMS_API_AUTH_TOKEN: str = "your_auth_token"
    SMS_API_TIMEOUT: float = 10.0
    SMS_API_MAX_RETRIES: int = 2
    
    # ========================================================================
    # External API: Email Service (SendGrid)
    # ========================================================================
    EMAIL_API_ENABLED: bool = True
    EMAIL_API_BASE_URL: str = "https://api.sendgrid.com/v3"
    EMAIL_API_KEY: str = "your_sendgrid_api_key"
    EMAIL_API_TIMEOUT: float = 15.0
    EMAIL_API_CACHE_ENABLED: bool = False  # Don't cache email sends
    
    # ========================================================================
    # External API: Weather Service
    # ========================================================================
    WEATHER_API_ENABLED: bool = False
    WEATHER_API_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
    WEATHER_API_KEY: str = "your_openweather_api_key"
    WEATHER_API_CACHE_ENABLED: bool = True
    WEATHER_API_CACHE_TTL: int = 600  # 10 minutes
    
    # ========================================================================
    # Kafka Settings (if using messaging)
    # ========================================================================
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    KAFKA_ENABLE_OUTBOX: bool = True
    KAFKA_ENABLE_INBOX: bool = True
    
    # ========================================================================
    # Observability Settings
    # ========================================================================
    OTLP_ENDPOINT: str = "http://localhost:4317"
    ENABLE_TRACING: bool = True
    ENABLE_METRICS: bool = True
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )
    
    # ========================================================================
    # Configuration Factory Methods
    # ========================================================================
    
    def get_redis_config(self) -> RedisConfig:
        """Get Redis configuration from settings."""
        return RedisConfig(
            host=self.REDIS_HOST,
            port=self.REDIS_PORT,
            db=self.REDIS_DB,
            password=self.REDIS_PASSWORD,
            username=self.REDIS_USERNAME,
            key_prefix=self.REDIS_KEY_PREFIX,
            default_ttl=self.REDIS_DEFAULT_TTL,
            max_connections=self.REDIS_MAX_CONNECTIONS,
            ssl=self.REDIS_SSL_ENABLED,
            health_check_interval=30,
        )
    
    def get_payment_api_config(self) -> ExternalApiConfig:
        """Get payment API configuration."""
        return ExternalApiConfig(
            name="stripe",
            base_url=self.PAYMENT_API_BASE_URL,
            auth_type="bearer",
            bearer_token=self.PAYMENT_API_TOKEN,
            timeout=self.PAYMENT_API_TIMEOUT,
            max_retries=self.PAYMENT_API_MAX_RETRIES,
            enable_circuit_breaker=True,
            circuit_breaker_threshold=5,
            circuit_breaker_timeout=60.0,
            enable_caching=self.PAYMENT_API_CACHE_ENABLED,
            cache_ttl=self.PAYMENT_API_CACHE_TTL,
            cache_key_prefix="stripe:",
            consumer_id=f"{self.APP_NAME}-payment",
        )
    
    def get_sms_api_config(self) -> ExternalApiConfig:
        """Get SMS API configuration (Twilio uses Basic Auth)."""
        return ExternalApiConfig(
            name="twilio",
            base_url=self.SMS_API_BASE_URL,
            auth_type="basic",
            basic_username=self.SMS_API_ACCOUNT_SID,
            basic_password=self.SMS_API_AUTH_TOKEN,
            timeout=self.SMS_API_TIMEOUT,
            max_retries=self.SMS_API_MAX_RETRIES,
            enable_circuit_breaker=True,
            enable_caching=False,  # Don't cache SMS sends
            consumer_id=f"{self.APP_NAME}-sms",
        )
    
    def get_email_api_config(self) -> ExternalApiConfig:
        """Get email API configuration."""
        return ExternalApiConfig(
            name="sendgrid",
            base_url=self.EMAIL_API_BASE_URL,
            auth_type="bearer",
            bearer_token=self.EMAIL_API_KEY,
            timeout=self.EMAIL_API_TIMEOUT,
            max_retries=2,
            enable_circuit_breaker=True,
            enable_caching=self.EMAIL_API_CACHE_ENABLED,
            consumer_id=f"{self.APP_NAME}-email",
        )
    
    def get_weather_api_config(self) -> ExternalApiConfig:
        """Get weather API configuration."""
        return ExternalApiConfig(
            name="openweather",
            base_url=self.WEATHER_API_BASE_URL,
            auth_type="api_key",
            api_key=self.WEATHER_API_KEY,
            api_key_header="appid",  # OpenWeather uses 'appid' param
            timeout=10.0,
            max_retries=2,
            enable_circuit_breaker=False,  # Weather is non-critical
            enable_caching=self.WEATHER_API_CACHE_ENABLED,
            cache_ttl=self.WEATHER_API_CACHE_TTL,
            cache_key_prefix="weather:",
            rate_limit_enabled=True,
            rate_limit_requests=60,  # Free tier limit
            rate_limit_period=60,
        )
    
    def get_all_external_apis(self) -> Dict[str, ExternalApiConfig]:
        """Get all configured external APIs."""
        apis = {}
        
        if self.PAYMENT_API_ENABLED:
            apis["payment"] = self.get_payment_api_config()
        
        if self.SMS_API_ENABLED:
            apis["sms"] = self.get_sms_api_config()
        
        if self.EMAIL_API_ENABLED:
            apis["email"] = self.get_email_api_config()
        
        if self.WEATHER_API_ENABLED:
            apis["weather"] = self.get_weather_api_config()
        
        return apis


# ============================================================================
# Global Settings Instance
# ============================================================================

settings = Settings()


# ============================================================================
# Usage Examples
# ============================================================================

def example_usage():
    """Example: How to use the configuration in your application."""
    
    # Get Redis config
    redis_config = settings.get_redis_config()
    print(f"Redis: {redis_config.host}:{redis_config.port}")
    
    # Get payment API config
    payment_config = settings.get_payment_api_config()
    print(f"Payment API: {payment_config.base_url}")
    
    # Get all external APIs
    external_apis = settings.get_all_external_apis()
    for name, config in external_apis.items():
        print(f"{name}: {config.base_url} (cache: {config.enable_caching})")


async def example_with_redis():
    """Example: Using Redis with the configuration."""
    from building_blocks.infrastructure.cache import RedisClient
    
    redis_config = settings.get_redis_config()
    
    async with RedisClient(redis_config) as cache:
        # Store user data
        await cache.set("user:123", {
            "id": 123,
            "name": "John Doe",
            "email": "john@example.com"
        })
        
        # Retrieve user data
        user = await cache.get("user:123")
        print(f"User: {user}")


async def example_with_http_client():
    """Example: Using HTTP client with external API config."""
    from building_blocks.infrastructure.http import (
        HttpClient, HttpClientConfig, BearerAuth
    )
    
    # Get payment API configuration
    payment_config = settings.get_payment_api_config()
    
    # Create HTTP client config from external API config
    http_config = HttpClientConfig(
        base_url=payment_config.base_url,
        auth_strategy=BearerAuth(payment_config.bearer_token),
        timeout=payment_config.timeout,
        consumer_id=payment_config.consumer_id,
        enable_circuit_breaker=payment_config.enable_circuit_breaker,
        circuit_breaker_failure_threshold=payment_config.circuit_breaker_threshold,
        circuit_breaker_timeout=payment_config.circuit_breaker_timeout,
    )
    
    async with HttpClient(http_config) as client:
        # Make API call
        response = await client.get("/customers")
        customers = response.json()
        print(f"Customers: {len(customers)}")


async def example_api_caching():
    """Example: Caching external API responses."""
    from building_blocks.infrastructure.cache import RedisClient
    from building_blocks.infrastructure.http import HttpClient, HttpClientConfig, ApiKeyAuth
    
    # Setup Redis
    redis_config = settings.get_redis_config()
    cache = RedisClient(redis_config)
    await cache.connect()
    
    # Setup Weather API
    weather_config = settings.get_weather_api_config()
    
    async def fetch_weather(city: str):
        """Fetch weather with caching."""
        cache_key = f"{weather_config.get_cache_key_prefix()}{city}"
        
        # Check cache
        cached = await cache.get(cache_key)
        if cached:
            print(f"Cache HIT for {city}")
            return cached
        
        print(f"Cache MISS for {city}, fetching from API...")
        
        # Fetch from API
        http_config = HttpClientConfig(
            base_url=weather_config.base_url,
            auth_strategy=ApiKeyAuth(
                api_key=weather_config.api_key,
                header_name=weather_config.api_key_header
            ),
            timeout=weather_config.timeout,
        )
        
        async with HttpClient(http_config) as client:
            response = await client.get(f"/weather?q={city}")
            data = response.json()
        
        # Cache result
        await cache.set(cache_key, data, ttl=weather_config.cache_ttl)
        
        return data
    
    # Usage
    weather1 = await fetch_weather("San Francisco")  # Cache miss
    weather2 = await fetch_weather("San Francisco")  # Cache hit
    
    await cache.disconnect()


if __name__ == "__main__":
    """Run examples."""
    import asyncio
    
    print("\n=== Configuration Example ===")
    example_usage()
    
    print("\n=== Redis Example ===")
    asyncio.run(example_with_redis())
    
    print("\n=== API Caching Example ===")
    asyncio.run(example_api_caching())
