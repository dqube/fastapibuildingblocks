"""
Log redaction utilities for masking sensitive data in logs.
"""

import re
from typing import Any, Dict, List, Set, Pattern, Union
from copy import deepcopy


# Default sensitive field patterns (case-insensitive)
DEFAULT_SENSITIVE_PATTERNS = {
    # Authentication & Authorization
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "api-key",
    "access_token",
    "refresh_token",
    "bearer",
    "authorization",
    "auth",
    
    # Personal Information
    "ssn",
    "social_security",
    "credit_card",
    "creditcard",
    "card_number",
    "cvv",
    "pin",
    "account_number",
    "routing_number",
    
    # Credentials
    "private_key",
    "privatekey",
    "public_key",
    "publickey",
    "certificate",
    "cert",
    "key",
    
    # Sensitive User Data
    "email",  # Optional - can be removed if emails aren't sensitive
    "phone",
    "address",
}


class RedactionFilter:
    """Filter to redact sensitive information from log records."""
    
    def __init__(
        self,
        sensitive_keys: Set[str] = None,
        sensitive_patterns: List[str] = None,
        mask_value: str = "***REDACTED***",
        mask_length: bool = True,
        case_sensitive: bool = False,
    ):
        """
        Initialize the redaction filter.
        
        Args:
            sensitive_keys: Set of exact field names to redact (case-insensitive by default)
            sensitive_patterns: List of regex patterns to match field names
            mask_value: Value to replace sensitive data with
            mask_length: If True, show partial length (e.g., "***REDACTED(8)***")
            case_sensitive: If True, perform case-sensitive field matching
        """
        self.mask_value = mask_value
        self.mask_length = mask_length
        self.case_sensitive = case_sensitive
        
        # Use default patterns if none provided
        if sensitive_keys is None:
            sensitive_keys = DEFAULT_SENSITIVE_PATTERNS.copy()
        
        # Convert to lowercase for case-insensitive matching
        if not case_sensitive:
            self.sensitive_keys = {key.lower() for key in sensitive_keys}
        else:
            self.sensitive_keys = set(sensitive_keys)
        
        # Compile regex patterns
        self.sensitive_patterns: List[Pattern] = []
        if sensitive_patterns:
            flags = 0 if case_sensitive else re.IGNORECASE
            self.sensitive_patterns = [
                re.compile(pattern, flags) for pattern in sensitive_patterns
            ]
    
    def _should_redact(self, key: str) -> bool:
        """
        Check if a key should be redacted.
        
        Args:
            key: Field name to check
            
        Returns:
            True if the key should be redacted
        """
        check_key = key if self.case_sensitive else key.lower()
        
        # Check exact matches
        if check_key in self.sensitive_keys:
            return True
        
        # Check regex patterns
        for pattern in self.sensitive_patterns:
            if pattern.search(key):
                return True
        
        return False
    
    def _mask_value(self, value: Any) -> str:
        """
        Create masked representation of a value.
        
        Args:
            value: Original value
            
        Returns:
            Masked string representation
        """
        if self.mask_length and isinstance(value, (str, bytes)):
            length = len(value)
            return f"{self.mask_value}({length})"
        return self.mask_value
    
    def redact_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively redact sensitive fields from a dictionary.
        
        Args:
            data: Dictionary to redact
            
        Returns:
            New dictionary with sensitive fields redacted
        """
        if not isinstance(data, dict):
            return data
        
        result = {}
        for key, value in data.items():
            if self._should_redact(key):
                # Redact the value
                result[key] = self._mask_value(value)
            elif isinstance(value, dict):
                # Recursively redact nested dictionaries
                result[key] = self.redact_dict(value)
            elif isinstance(value, list):
                # Redact items in lists
                result[key] = self.redact_list(value)
            else:
                # Keep non-sensitive values
                result[key] = value
        
        return result
    
    def redact_list(self, data: List[Any]) -> List[Any]:
        """
        Recursively redact sensitive fields from a list.
        
        Args:
            data: List to redact
            
        Returns:
            New list with sensitive fields redacted
        """
        if not isinstance(data, list):
            return data
        
        result = []
        for item in data:
            if isinstance(item, dict):
                result.append(self.redact_dict(item))
            elif isinstance(item, list):
                result.append(self.redact_list(item))
            else:
                result.append(item)
        
        return result
    
    def redact_string(self, text: str) -> str:
        """
        Redact sensitive patterns from a string (e.g., log message).
        
        This attempts to find and redact common sensitive patterns like:
        - Bearer tokens
        - API keys in URLs
        - JSON with sensitive fields
        
        Args:
            text: String to redact
            
        Returns:
            String with sensitive patterns redacted
        """
        if not isinstance(text, str):
            return text
        
        # Redact Bearer tokens
        text = re.sub(
            r'Bearer\s+[A-Za-z0-9\-._~+/]+=*',
            f'Bearer {self.mask_value}',
            text,
            flags=re.IGNORECASE
        )
        
        # Redact API keys in URLs (e.g., ?api_key=xxx or &apikey=xxx)
        text = re.sub(
            r'([?&])(api[-_]?key|token|secret)=[^&\s]+',
            rf'\1\2={self.mask_value}',
            text,
            flags=re.IGNORECASE
        )
        
        # Redact Authorization headers (capture the full value including scheme and token)
        text = re.sub(
            r'Authorization:\s*[^\n,;]+',
            f'Authorization: {self.mask_value}',
            text,
            flags=re.IGNORECASE
        )
        
        return text
    
    def redact(self, data: Any) -> Any:
        """
        Redact sensitive information from any data type.
        
        Args:
            data: Data to redact (dict, list, str, or other)
            
        Returns:
            Redacted data
        """
        if isinstance(data, dict):
            return self.redact_dict(data)
        elif isinstance(data, list):
            return self.redact_list(data)
        elif isinstance(data, str):
            return self.redact_string(data)
        else:
            return data


def create_redaction_filter(
    additional_keys: List[str] = None,
    additional_patterns: List[str] = None,
    exclude_defaults: bool = False,
    mask_value: str = "***REDACTED***",
    mask_length: bool = True,
) -> RedactionFilter:
    """
    Create a redaction filter with custom configuration.
    
    Args:
        additional_keys: Additional sensitive field names to redact
        additional_patterns: Additional regex patterns for field names
        exclude_defaults: If True, don't use default sensitive patterns
        mask_value: Custom mask value
        mask_length: If True, show length of masked values
        
    Returns:
        Configured RedactionFilter instance
        
    Example:
        # Use defaults plus custom fields
        filter = create_redaction_filter(
            additional_keys=["user_id", "internal_id"],
            additional_patterns=[r".*_secret$", r"^private_.*"]
        )
        
        # Only use custom fields (no defaults)
        filter = create_redaction_filter(
            additional_keys=["password", "token"],
            exclude_defaults=True
        )
    """
    sensitive_keys = set() if exclude_defaults else DEFAULT_SENSITIVE_PATTERNS.copy()
    
    if additional_keys:
        sensitive_keys.update(additional_keys)
    
    return RedactionFilter(
        sensitive_keys=sensitive_keys,
        sensitive_patterns=additional_patterns,
        mask_value=mask_value,
        mask_length=mask_length,
    )
