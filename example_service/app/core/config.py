"""Application configuration."""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from fastapi_building_blocks.infrastructure.messaging import KafkaConfig


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "User Management Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
    ]
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/user_management"
    
    # Kafka Inbox/Outbox Patterns
    KAFKA_ENABLE_OUTBOX: bool = True  # Save events to outbox before publishing
    KAFKA_ENABLE_INBOX: bool = True   # Save incoming messages to inbox for idempotency
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


# Create global settings instance
settings = Settings()

# Create Kafka configuration
kafka_config = KafkaConfig(
    bootstrap_servers="kafka:9092",
    service_name=settings.APP_NAME,
    consumer_group_id="user-management-service",
    enable_outbox=settings.KAFKA_ENABLE_OUTBOX,
    enable_inbox=settings.KAFKA_ENABLE_INBOX,
)
