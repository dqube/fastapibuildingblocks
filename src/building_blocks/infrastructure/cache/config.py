"""
Redis Cache Configuration

Configurable Redis client settings for caching and data storage.
"""

from typing import Optional
from dataclasses import dataclass, field


@dataclass
class RedisConfig:
    """Redis client configuration."""
    
    # Connection settings
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    username: Optional[str] = None
    
    # Connection pool settings
    max_connections: int = 50
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    socket_keepalive: bool = True
    
    # Retry settings
    retry_on_timeout: bool = True
    retry_on_error: bool = True
    max_retry_attempts: int = 3
    
    # SSL/TLS settings
    ssl: bool = False
    ssl_cert_reqs: str = "required"
    ssl_ca_certs: Optional[str] = None
    ssl_certfile: Optional[str] = None
    ssl_keyfile: Optional[str] = None
    
    # Cache settings
    default_ttl: int = 3600  # 1 hour in seconds
    key_prefix: str = ""  # Optional prefix for all keys
    
    # Encoding
    encoding: str = "utf-8"
    decode_responses: bool = True
    
    # Health check
    health_check_interval: int = 30  # seconds
    
    # Cluster settings
    cluster_enabled: bool = False
    cluster_nodes: list = field(default_factory=list)
    
    # Sentinel settings (for high availability)
    sentinel_enabled: bool = False
    sentinel_nodes: list = field(default_factory=list)
    sentinel_master_name: Optional[str] = None


@dataclass
class ExternalApiConfig:
    """Configuration for external API integration."""
    
    # API identification
    name: str  # Unique name for this API
    base_url: str
    
    # Authentication
    auth_type: str = "none"  # none, bearer, basic, api_key, oauth2, custom
    
    # Auth credentials
    bearer_token: Optional[str] = None
    basic_username: Optional[str] = None
    basic_password: Optional[str] = None
    api_key: Optional[str] = None
    api_key_header: str = "X-API-Key"
    oauth2_token_url: Optional[str] = None
    oauth2_client_id: Optional[str] = None
    oauth2_client_secret: Optional[str] = None
    oauth2_scope: Optional[str] = None
    custom_headers: dict = field(default_factory=dict)
    
    # Request settings
    timeout: float = 30.0
    max_retries: int = 3
    retry_backoff_factor: float = 0.5
    
    # Circuit breaker
    enable_circuit_breaker: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0
    
    # Caching
    enable_caching: bool = False
    cache_ttl: int = 300  # 5 minutes
    cache_key_prefix: Optional[str] = None
    
    # Rate limiting
    rate_limit_enabled: bool = False
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds
    
    # Monitoring
    consumer_id: Optional[str] = None
    
    def get_cache_key_prefix(self) -> str:
        """Get cache key prefix for this API."""
        return self.cache_key_prefix or f"api:{self.name}:"
