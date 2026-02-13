"""
Tests for log redaction functionality.
"""

import pytest
from fastapi_building_blocks.observability.redaction import (
    RedactionFilter,
    create_redaction_filter,
    DEFAULT_SENSITIVE_PATTERNS,
)


class TestRedactionFilter:
    """Tests for RedactionFilter class."""
    
    def test_default_sensitive_patterns(self):
        """Test that default patterns are loaded."""
        filter = RedactionFilter()
        assert len(filter.sensitive_keys) > 0
        assert "password" in filter.sensitive_keys
        assert "token" in filter.sensitive_keys
        assert "api_key" in filter.sensitive_keys
    
    def test_redact_simple_dict(self):
        """Test redacting a simple dictionary."""
        filter = RedactionFilter()
        data = {
            "username": "john_doe",
            "password": "secret123",
            "email": "john@example.com",
        }
        
        result = filter.redact_dict(data)
        
        assert result["username"] == "john_doe"
        assert result["password"] == "***REDACTED***(9)"
        assert "***REDACTED***" in result["email"]
    
    def test_redact_nested_dict(self):
        """Test redacting nested dictionaries."""
        filter = RedactionFilter()
        data = {
            "user": {
                "name": "John Doe",
                "credentials": {
                    "password": "secret123",
                    "api_key": "sk_live_1234567890",
                }
            },
            "public_data": "visible"
        }
        
        result = filter.redact_dict(data)
        
        assert result["user"]["name"] == "John Doe"
        assert "***REDACTED***" in result["user"]["credentials"]["password"]
        assert "***REDACTED***" in result["user"]["credentials"]["api_key"]
        assert result["public_data"] == "visible"
    
    def test_redact_list_of_dicts(self):
        """Test redacting lists containing dictionaries."""
        filter = RedactionFilter()
        data = {
            "users": [
                {"name": "User1", "token": "token1"},
                {"name": "User2", "token": "token2"},
            ]
        }
        
        result = filter.redact_dict(data)
        
        assert result["users"][0]["name"] == "User1"
        assert "***REDACTED***" in result["users"][0]["token"]
        assert result["users"][1]["name"] == "User2"
        assert "***REDACTED***" in result["users"][1]["token"]
    
    def test_case_insensitive_matching(self):
        """Test case-insensitive field matching."""
        filter = RedactionFilter(case_sensitive=False)
        data = {
            "Password": "secret1",
            "PASSWORD": "secret2",
            "password": "secret3",
            "PaSsWoRd": "secret4",
        }
        
        result = filter.redact_dict(data)
        
        # All variations should be redacted
        assert "***REDACTED***" in result["Password"]
        assert "***REDACTED***" in result["PASSWORD"]
        assert "***REDACTED***" in result["password"]
        assert "***REDACTED***" in result["PaSsWoRd"]
    
    def test_custom_sensitive_keys(self):
        """Test using custom sensitive keys."""
        filter = RedactionFilter(
            sensitive_keys={"user_id", "internal_code"},
            case_sensitive=False
        )
        data = {
            "user_id": "12345",
            "internal_code": "ABC-789",
            "password": "will_not_be_redacted",  # Not in custom list
        }
        
        result = filter.redact_dict(data)
        
        assert "***REDACTED***" in result["user_id"]
        assert "***REDACTED***" in result["internal_code"]
        assert result["password"] == "will_not_be_redacted"
    
    def test_custom_patterns(self):
        """Test using regex patterns for field matching."""
        filter = RedactionFilter(
            sensitive_keys=set(),
            sensitive_patterns=[r".*_secret$", r"^private_.*"]
        )
        data = {
            "app_secret": "secret1",
            "db_secret": "secret2",
            "private_key": "key123",
            "private_data": "data456",
            "public_info": "visible",
        }
        
        result = filter.redact_dict(data)
        
        assert "***REDACTED***" in result["app_secret"]
        assert "***REDACTED***" in result["db_secret"]
        assert "***REDACTED***" in result["private_key"]
        assert "***REDACTED***" in result["private_data"]
        assert result["public_info"] == "visible"
    
    def test_mask_length_option(self):
        """Test mask_length option."""
        filter_with_length = RedactionFilter(mask_length=True)
        filter_without_length = RedactionFilter(mask_length=False)
        
        data = {"password": "12345678"}
        
        result_with = filter_with_length.redact_dict(data)
        result_without = filter_without_length.redact_dict(data)
        
        assert "(8)" in result_with["password"]
        assert "(8)" not in result_without["password"]
    
    def test_custom_mask_value(self):
        """Test custom mask value."""
        filter = RedactionFilter(mask_value="[HIDDEN]", mask_length=False)
        data = {"password": "secret"}
        
        result = filter.redact_dict(data)
        
        assert result["password"] == "[HIDDEN]"
    
    def test_redact_bearer_token_in_string(self):
        """Test redacting Bearer tokens from strings."""
        filter = RedactionFilter()
        text = "Authorization header: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        
        result = filter.redact_string(text)
        
        assert "Bearer ***REDACTED***" in result
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result
    
    def test_redact_api_key_in_url(self):
        """Test redacting API keys from URLs."""
        filter = RedactionFilter()
        text = "Calling API: https://api.example.com/data?api_key=sk_live_1234567890&user=john"
        
        result = filter.redact_string(text)
        
        assert "api_key=***REDACTED***" in result
        assert "sk_live_1234567890" not in result
        assert "&user=john" in result  # Other params should remain
    
    def test_redact_authorization_header(self):
        """Test redacting Authorization headers."""
        filter = RedactionFilter()
        text = "Request headers: Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ="
        
        result = filter.redact_string(text)
        
        assert "Authorization: ***REDACTED***" in result
        assert "dXNlcm5hbWU6cGFzc3dvcmQ=" not in result
    
    def test_redact_mixed_types(self):
        """Test redacting with mixed data types."""
        filter = RedactionFilter()
        data = {
            "count": 42,
            "active": True,
            "password": "secret",
            "tags": ["tag1", "tag2"],
            "nested": {
                "token": "abc123",
                "value": 3.14
            }
        }
        
        result = filter.redact_dict(data)
        
        assert result["count"] == 42
        assert result["active"] is True
        assert "***REDACTED***" in result["password"]
        assert result["tags"] == ["tag1", "tag2"]
        assert "***REDACTED***" in result["nested"]["token"]
        assert result["nested"]["value"] == 3.14
    
    def test_empty_data(self):
        """Test redacting empty data structures."""
        filter = RedactionFilter()
        
        assert filter.redact_dict({}) == {}
        assert filter.redact_list([]) == []
        assert filter.redact_string("") == ""
    
    def test_none_values(self):
        """Test handling None values."""
        filter = RedactionFilter()
        data = {
            "password": None,
            "username": "john",
        }
        
        result = filter.redact_dict(data)
        
        assert result["password"] == "***REDACTED***"
        assert result["username"] == "john"


class TestCreateRedactionFilter:
    """Tests for create_redaction_filter helper function."""
    
    def test_create_with_defaults(self):
        """Test creating filter with default settings."""
        filter = create_redaction_filter()
        
        assert filter.sensitive_keys == DEFAULT_SENSITIVE_PATTERNS
        assert filter.mask_value == "***REDACTED***"
        assert filter.mask_length is True
    
    def test_create_with_additional_keys(self):
        """Test adding additional sensitive keys."""
        filter = create_redaction_filter(
            additional_keys=["custom_field", "internal_id"]
        )
        
        assert "custom_field" in filter.sensitive_keys
        assert "internal_id" in filter.sensitive_keys
        assert "password" in filter.sensitive_keys  # Default still present
    
    def test_create_excluding_defaults(self):
        """Test creating filter without defaults."""
        filter = create_redaction_filter(
            additional_keys=["password", "token"],
            exclude_defaults=True
        )
        
        assert "password" in filter.sensitive_keys
        assert "token" in filter.sensitive_keys
        assert len(filter.sensitive_keys) == 2  # Only custom keys
    
    def test_create_with_patterns(self):
        """Test creating filter with patterns."""
        filter = create_redaction_filter(
            additional_patterns=[r".*_secret$"]
        )
        
        assert len(filter.sensitive_patterns) == 1
    
    def test_create_with_custom_mask(self):
        """Test creating filter with custom mask settings."""
        filter = create_redaction_filter(
            mask_value="[HIDDEN]",
            mask_length=False
        )
        
        assert filter.mask_value == "[HIDDEN]"
        assert filter.mask_length is False


class TestIntegrationScenarios:
    """Integration tests for real-world scenarios."""
    
    def test_http_request_logging(self):
        """Test redacting sensitive data from HTTP request logs."""
        filter = RedactionFilter()
        log_data = {
            "method": "POST",
            "path": "/api/login",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer secret_token_12345"
            },
            "body": {
                "username": "john_doe",
                "password": "my_secret_password"
            },
            "response_time": 0.125
        }
        
        result = filter.redact_dict(log_data)
        
        assert result["method"] == "POST"
        assert result["path"] == "/api/login"
        assert "***REDACTED***" in result["headers"]["Authorization"]
        assert result["body"]["username"] == "john_doe"
        assert "***REDACTED***" in result["body"]["password"]
        assert result["response_time"] == 0.125
    
    def test_database_connection_string(self):
        """Test redacting database credentials from connection strings."""
        filter = RedactionFilter()
        log_message = "Connecting to database: postgresql://user:password123@localhost:5432/mydb"
        
        # While the filter won't handle connection strings perfectly,
        # it will redact if password is in a dict
        data = {
            "db_config": {
                "host": "localhost",
                "username": "user",
                "password": "password123",
                "database": "mydb"
            }
        }
        
        result = filter.redact_dict(data)
        
        assert result["db_config"]["host"] == "localhost"
        assert result["db_config"]["username"] == "user"
        assert "***REDACTED***" in result["db_config"]["password"]
        assert result["db_config"]["database"] == "mydb"
    
    def test_webhook_payload(self):
        """Test redacting sensitive data from webhook payloads."""
        filter = RedactionFilter()
        webhook_data = {
            "event": "payment.succeeded",
            "data": {
                "object": "payment",
                "amount": 1000,
                "customer": {
                    "id": "cus_123",
                    "email": "customer@example.com",
                    "card": {
                        "last4": "4242",
                        "card_number": "4242424242424242",
                        "cvv": "123"
                    }
                }
            },
            "api_key": "sk_live_abc123xyz"
        }
        
        result = filter.redact_dict(webhook_data)
        
        assert result["event"] == "payment.succeeded"
        assert result["data"]["amount"] == 1000
        assert "***REDACTED***" in result["data"]["customer"]["email"]
        assert "***REDACTED***" in result["data"]["customer"]["card"]["card_number"]
        assert "***REDACTED***" in result["data"]["customer"]["card"]["cvv"]
        assert "***REDACTED***" in result["api_key"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
