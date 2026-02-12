"""Base class for external service integrations."""

from abc import ABC
from typing import Optional


class ExternalService(ABC):
    """
    Base class for external service integrations.
    
    This class provides a base for integrating with third-party services
    and external APIs.
    """
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize the external service.
        
        Args:
            base_url: The base URL of the external service
            api_key: The API key for authentication
        """
        self.base_url = base_url
        self.api_key = api_key
    
    def get_headers(self) -> dict:
        """
        Get the headers for API requests.
        
        Returns:
            Dictionary of headers
        """
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
