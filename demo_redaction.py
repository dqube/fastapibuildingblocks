"""
Demonstration of log redaction functionality.
Shows how sensitive data is automatically masked in logs.
"""

import logging
from src.building_blocks.observability import (
    ObservabilityConfig,
    setup_logging,
    get_logger,
)

# Examples to demonstrate
EXAMPLES = [
    {
        "title": "1. User Authentication Request",
        "data": {
            "event": "user_login",
            "username": "john_doe",
            "password": "MySecretPassword123!",
            "api_key": "sk_live_1234567890abcdef",
            "timestamp": "2024-01-15T10:30:00Z"
        }
    },
    {
        "title": "2. Payment Processing",
        "data": {
            "transaction_id": "txn_abc123",
            "amount": 99.99,
            "customer": {
                "name": "Jane Smith",
                "email": "jane@example.com",
                "credit_card": "4532-1234-5678-9012",
                "cvv": "123",
                "ssn": "123-45-6789"
            }
        }
    },
    {
        "title": "3. API Call with Headers",
        "data": {
            "method": "POST",
            "url": "https://api.example.com/users",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0",
                "X-API-Key": "secret_key_abc123"
            },
            "body": {
                "username": "newuser",
                "password": "SecurePass456",
                "email": "user@example.com"
            }
        }
    },
    {
        "title": "4. Database Configuration",
        "data": {
            "database": {
                "host": "localhost",
                "port": 5432,
                "username": "app_user",
                "password": "dbPassword123",
                "database_name": "production_db",
                "ssl_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQ..."
            }
        }
    },
    {
        "title": "5. OAuth Token Exchange",
        "data": {
            "grant_type": "authorization_code",
            "code": "auth_code_xyz789",
            "client_id": "client_12345",
            "client_secret": "super_secret_client_secret",
            "access_token": "ya29.a0AfH6SMBx...",
            "refresh_token": "1//0gPK4...",
            "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjFlOWdkazcifQ..."
        }
    },
    {
        "title": "6. AWS Credentials",
        "data": {
            "service": "s3",
            "region": "us-east-1",
            "credentials": {
                "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
                "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "session_token": "FwoGZXIvYXdzEH0aDC..."
            }
        }
    }
]


def demo_with_redaction():
    """Demonstrate logging WITH redaction enabled."""
    print("\n" + "="*80)
    print("DEMONSTRATION: LOG REDACTION ENABLED")
    print("="*80)
    
    # Configure observability with redaction
    config = ObservabilityConfig(
        service_name="demo-service",
        logging_enabled=True,
        log_format="json",
        log_level="INFO",
        log_redaction_enabled=True,  # Redaction ON
        redaction_mask_value="***REDACTED***",
        redaction_mask_length=True,
        # Add custom sensitive keys
        sensitive_field_keys=["transaction_id", "customer_id"]
    )
    
    setup_logging(config)
    logger = get_logger("demo")
    
    for example in EXAMPLES:
        print(f"\n{example['title']}")
        print("-" * 80)
        logger.info(f"{example['title']}", extra={"extra_fields": example['data']})
        print()


def demo_without_redaction():
    """Demonstrate logging WITHOUT redaction (DANGEROUS!)."""
    print("\n" + "="*80)
    print("DEMONSTRATION: LOG REDACTION DISABLED (UNSAFE)")
    print("="*80)
    print("⚠️  WARNING: Sensitive data will be exposed in logs!")
    print("="*80)
    
    # Reset logging
    logging.getLogger().handlers.clear()
    
    # Configure observability WITHOUT redaction
    config = ObservabilityConfig(
        service_name="demo-service",
        logging_enabled=True,
        log_format="json",
        log_level="INFO",
        log_redaction_enabled=False,  # Redaction OFF - DANGEROUS!
    )
    
    setup_logging(config)
    logger = get_logger("demo")
    
    # Only show first example to demonstrate the danger
    example = EXAMPLES[0]
    print(f"\n{example['title']}")
    print("-" * 80)
    logger.info(f"{example['title']}", extra={"extra_fields": example['data']})
    print()


def demo_custom_patterns():
    """Demonstrate custom sensitive field patterns."""
    print("\n" + "="*80)
    print("DEMONSTRATION: CUSTOM REDACTION PATTERNS")
    print("="*80)
    
    # Reset logging
    logging.getLogger().handlers.clear()
    
    # Configure with custom patterns
    config = ObservabilityConfig(
        service_name="demo-service",
        logging_enabled=True,
        log_format="json",
        log_level="INFO",
        log_redaction_enabled=True,
        # Custom patterns to match fields ending with _id or starting with internal_
        sensitive_field_patterns=[
            r".*_id$",           # Match any field ending with _id
            r"^internal_.*",     # Match any field starting with internal_
            r".*_secret$",       # Match any field ending with _secret
        ]
    )
    
    setup_logging(config)
    logger = get_logger("demo")
    
    data = {
        "user_id": "12345",              # Will be redacted (_id pattern)
        "customer_id": "cust_789",       # Will be redacted (_id pattern)
        "internal_code": "ABC-123",      # Will be redacted (internal_ pattern)
        "internal_reference": "REF-456", # Will be redacted (internal_ pattern)
        "app_secret": "secret123",       # Will be redacted (_secret pattern)
        "username": "john_doe",          # NOT redacted
        "amount": 99.99,                 # NOT redacted
    }
    
    print("\nLogging data with custom patterns:")
    print("-" * 80)
    logger.info("Custom pattern test", extra={"extra_fields": data})
    print()


def demo_string_redaction():
    """Demonstrate string-based redaction for Bearer tokens and API keys."""
    print("\n" + "="*80)
    print("DEMONSTRATION: STRING PATTERN REDACTION")
    print("="*80)
    
    # Reset logging
    logging.getLogger().handlers.clear()
    
    config = ObservabilityConfig(
        service_name="demo-service",
        logging_enabled=True,
        log_format="text",  # Using text format to show string redaction
        log_level="INFO",
        log_redaction_enabled=True,
    )
    
    setup_logging(config)
    logger = get_logger("demo")
    
    messages = [
        "API request with Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0",
        "Calling API: https://api.example.com/data?api_key=sk_live_1234567890&user=john",
        "Request headers: Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=",
        "Using token: Bearer abc123xyz and key: api_key=secret789 for authentication",
    ]
    
    print("\nString-based redaction in log messages:")
    print("-" * 80)
    for msg in messages:
        logger.info(msg)
    print()


if __name__ == "__main__":
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " " * 20 + "LOG REDACTION DEMONSTRATION" + " " * 31 + "║")
    print("╚" + "="*78 + "╝")
    
    # Show redacted logs (safe)
    demo_with_redaction()
    
    input("\n▶ Press Enter to see the DANGER of disabled redaction...")
    
    # Show unredacted logs (dangerous)
    demo_without_redaction()
    
    input("\n▶ Press Enter to see custom pattern redaction...")
    
    # Show custom patterns
    demo_custom_patterns()
    
    input("\n▶ Press Enter to see string pattern redaction...")
    
    # Show string redaction
    demo_string_redaction()
    
    print("\n" + "="*80)
    print("SUMMARY:")
    print("="*80)
    print("✅ Redaction successfully masks: passwords, tokens, API keys, secrets,")
    print("   credit cards, SSNs, emails, private keys, and more.")
    print()
    print("✅ Supports custom sensitive field patterns (regex)")
    print()
    print("✅ Redacts Bearer tokens, API keys in URLs, and Authorization headers")
    print("   from string messages")
    print()
    print("✅ Recursive redaction for nested dictionaries and lists")
    print()
    print("⚠️  ALWAYS keep log_redaction_enabled=True in production!")
    print("="*80)
    print()
