"""Kafka configuration for integration events."""

from typing import Dict, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class KafkaConfig(BaseSettings):
    """
    Configuration for Kafka integration.
    
    This configuration supports both producer and consumer settings.
    Values can be set via environment variables with KAFKA_ prefix.
    """
    
    # Connection settings
    bootstrap_servers: str = Field(
        default="localhost:9092",
        description="Comma-separated list of Kafka broker addresses"
    )
    
    # Security settings
    security_protocol: str = Field(
        default="PLAINTEXT",
        description="Protocol used to communicate with brokers (PLAINTEXT, SSL, SASL_PLAINTEXT, SASL_SSL)"
    )
    sasl_mechanism: Optional[str] = Field(
        default=None,
        description="SASL mechanism (PLAIN, SCRAM-SHA-256, SCRAM-SHA-512)"
    )
    sasl_username: Optional[str] = Field(default=None, description="SASL username")
    sasl_password: Optional[str] = Field(default=None, description="SASL password")
    
    # SSL settings
    ssl_cafile: Optional[str] = Field(default=None, description="Path to CA certificate file")
    ssl_certfile: Optional[str] = Field(default=None, description="Path to client certificate file")
    ssl_keyfile: Optional[str] = Field(default=None, description="Path to client private key file")
    
    # Producer settings
    producer_acks: str = Field(
        default="all",
        description="Number of acknowledgments the producer requires (0, 1, all)"
    )
    producer_compression_type: Optional[str] = Field(
        default="gzip",
        description="Compression type for producer (none, gzip, snappy, lz4, zstd)"
    )
    producer_max_request_size: int = Field(
        default=1048576,  # 1MB
        description="Maximum size of a request in bytes"
    )
    producer_retries: int = Field(
        default=3,
        description="Number of retries for failed produce requests"
    )
    producer_batch_size: int = Field(
        default=16384,  # 16KB
        description="Number of bytes to batch before sending"
    )
    producer_linger_ms: int = Field(
        default=10,
        description="Time to wait before sending batch (milliseconds)"
    )
    
    # Consumer settings
    consumer_group_id: str = Field(
        default="fastapi-service",
        description="Consumer group ID"
    )
    consumer_auto_offset_reset: str = Field(
        default="earliest",
        description="Where to start reading messages (earliest, latest)"
    )
    consumer_enable_auto_commit: bool = Field(
        default=False,
        description="Whether to auto-commit offsets"
    )
    consumer_max_poll_records: int = Field(
        default=500,
        description="Maximum number of records per poll"
    )
    consumer_session_timeout_ms: int = Field(
        default=30000,  # 30 seconds
        description="Consumer session timeout in milliseconds"
    )
    consumer_heartbeat_interval_ms: int = Field(
        default=10000,  # 10 seconds
        description="Heartbeat interval in milliseconds"
    )
    
    # Application settings
    service_name: str = Field(
        default="fastapi-service",
        description="Name of this service (used in event metadata)"
    )
    default_topic_prefix: str = Field(
        default="integration-events",
        description="Default prefix for integration event topics"
    )
    enable_idempotence: bool = Field(
        default=True,
        description="Enable idempotent producer"
    )
    enable_observability: bool = Field(
        default=True,
        description="Enable OpenTelemetry tracing and metrics"
    )
    
    # Inbox/Outbox pattern settings
    enable_outbox: bool = Field(
        default=False,
        description="Enable transactional outbox pattern for publishing (stores events in database before publishing)"
    )
    enable_inbox: bool = Field(
        default=False,
        description="Enable inbox pattern for consuming (ensures exactly-once processing via database)"
    )
    
    # Dead letter queue settings
    enable_dlq: bool = Field(
        default=True,
        description="Enable dead letter queue for failed messages"
    )
    dlq_topic_suffix: str = Field(
        default=".dlq",
        description="Suffix for dead letter queue topics"
    )
    max_retry_attempts: int = Field(
        default=3,
        description="Maximum retry attempts before sending to DLQ"
    )
    
    class Config:
        """Pydantic settings configuration."""
        env_prefix = "KAFKA_"
        case_sensitive = False
    
    def get_producer_config(self) -> Dict[str, any]:
        """
        Get Kafka producer configuration dictionary.
        
        Returns:
            Dictionary of producer configuration
        """
        config = {
            'bootstrap_servers': self.bootstrap_servers.split(','),
            'acks': self.producer_acks,
            'compression_type': self.producer_compression_type,
            'max_request_size': self.producer_max_request_size,
            # Note: 'retries' removed - aiokafka uses request_timeout_ms instead
            'request_timeout_ms': 30000,  # 30 seconds timeout
            'max_batch_size': self.producer_batch_size,
            'linger_ms': self.producer_linger_ms,
            'enable_idempotence': self.enable_idempotence,
            'security_protocol': self.security_protocol,
        }
        
        # Add SASL configuration if specified
        if self.sasl_mechanism:
            config['sasl_mechanism'] = self.sasl_mechanism
            config['sasl_plain_username'] = self.sasl_username
            config['sasl_plain_password'] = self.sasl_password
        
        # Add SSL configuration if specified
        if self.ssl_cafile:
            config['ssl_cafile'] = self.ssl_cafile
        if self.ssl_certfile:
            config['ssl_certfile'] = self.ssl_certfile
        if self.ssl_keyfile:
            config['ssl_keyfile'] = self.ssl_keyfile
        
        return config
    
    def get_consumer_config(self) -> Dict[str, any]:
        """
        Get Kafka consumer configuration dictionary.
        
        Returns:
            Dictionary of consumer configuration
        """
        config = {
            'bootstrap_servers': self.bootstrap_servers.split(','),
            'group_id': self.consumer_group_id,
            'auto_offset_reset': self.consumer_auto_offset_reset,
            'enable_auto_commit': self.consumer_enable_auto_commit,
            'max_poll_records': self.consumer_max_poll_records,
            'session_timeout_ms': self.consumer_session_timeout_ms,
            'heartbeat_interval_ms': self.consumer_heartbeat_interval_ms,
            'security_protocol': self.security_protocol,
        }
        
        # Add SASL configuration if specified
        if self.sasl_mechanism:
            config['sasl_mechanism'] = self.sasl_mechanism
            config['sasl_plain_username'] = self.sasl_username
            config['sasl_plain_password'] = self.sasl_password
        
        # Add SSL configuration if specified
        if self.ssl_cafile:
            config['ssl_cafile'] = self.ssl_cafile
        if self.ssl_certfile:
            config['ssl_certfile'] = self.ssl_certfile
        if self.ssl_keyfile:
            config['ssl_keyfile'] = self.ssl_keyfile
        
        return config
