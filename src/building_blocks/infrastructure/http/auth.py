"""
HTTP Authentication Strategies

Provides various authentication strategies for HTTP clients.
"""

import base64
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict
from datetime import datetime, timedelta

import httpx

logger = logging.getLogger(__name__)


class AuthStrategy(ABC):
    """Base class for authentication strategies."""
    
    @abstractmethod
    async def apply_auth(self, request: httpx.Request) -> None:
        """
        Apply authentication to the request.
        
        Args:
            request: The HTTP request to authenticate
        """
        pass
    
    @abstractmethod
    async def refresh_if_needed(self) -> None:
        """Refresh authentication credentials if needed."""
        pass


class NoAuth(AuthStrategy):
    """No authentication strategy."""
    
    async def apply_auth(self, request: httpx.Request) -> None:
        """No authentication applied."""
        pass
    
    async def refresh_if_needed(self) -> None:
        """No refresh needed."""
        pass


class BearerAuth(AuthStrategy):
    """Bearer token authentication (e.g., JWT)."""
    
    def __init__(self, token: str):
        """
        Initialize bearer authentication.
        
        Args:
            token: Bearer token
        """
        self.token = token
    
    async def apply_auth(self, request: httpx.Request) -> None:
        """Apply bearer token to request."""
        request.headers["Authorization"] = f"Bearer {self.token}"
    
    async def refresh_if_needed(self) -> None:
        """Override in subclass to implement token refresh."""
        pass


class BasicAuth(AuthStrategy):
    """HTTP Basic authentication."""
    
    def __init__(self, username: str, password: str):
        """
        Initialize basic authentication.
        
        Args:
            username: Username
            password: Password
        """
        self.username = username
        self.password = password
        self._encoded_credentials = self._encode_credentials()
    
    def _encode_credentials(self) -> str:
        """Encode credentials in base64."""
        credentials = f"{self.username}:{self.password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return encoded
    
    async def apply_auth(self, request: httpx.Request) -> None:
        """Apply basic authentication to request."""
        request.headers["Authorization"] = f"Basic {self._encoded_credentials}"
    
    async def refresh_if_needed(self) -> None:
        """No refresh needed for basic auth."""
        pass


class ApiKeyAuth(AuthStrategy):
    """API Key authentication (header or query parameter)."""
    
    def __init__(
        self,
        api_key: str,
        header_name: str = "X-API-Key",
        location: str = "header"
    ):
        """
        Initialize API key authentication.
        
        Args:
            api_key: API key value
            header_name: Header name for the API key (if location is 'header')
            location: Where to put the key ('header' or 'query')
        """
        self.api_key = api_key
        self.header_name = header_name
        self.location = location
    
    async def apply_auth(self, request: httpx.Request) -> None:
        """Apply API key to request."""
        if self.location == "header":
            request.headers[self.header_name] = self.api_key
        elif self.location == "query":
            # Add to query params
            url = str(request.url)
            separator = "&" if "?" in url else "?"
            request.url = httpx.URL(f"{url}{separator}api_key={self.api_key}")
    
    async def refresh_if_needed(self) -> None:
        """No refresh needed for API key."""
        pass


class OAuth2ClientCredentials(AuthStrategy):
    """OAuth 2.0 Client Credentials flow."""
    
    def __init__(
        self,
        token_url: str,
        client_id: str,
        client_secret: str,
        scope: Optional[str] = None
    ):
        """
        Initialize OAuth2 client credentials authentication.
        
        Args:
            token_url: OAuth2 token endpoint URL
            client_id: Client ID
            client_secret: Client secret
            scope: Optional scope
        """
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
    
    async def apply_auth(self, request: httpx.Request) -> None:
        """Apply OAuth2 token to request."""
        await self.refresh_if_needed()
        
        if self.access_token:
            request.headers["Authorization"] = f"Bearer {self.access_token}"
    
    async def refresh_if_needed(self) -> None:
        """Refresh OAuth2 token if expired or missing."""
        if self._is_token_expired():
            await self._fetch_token()
    
    def _is_token_expired(self) -> bool:
        """Check if token is expired."""
        if not self.access_token or not self.token_expires_at:
            return True
        
        # Refresh 5 minutes before expiration
        return datetime.utcnow() >= (self.token_expires_at - timedelta(minutes=5))
    
    async def _fetch_token(self) -> None:
        """Fetch new access token."""
        try:
            async with httpx.AsyncClient() as client:
                data = {
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                }
                
                if self.scope:
                    data["scope"] = self.scope
                
                response = await client.post(
                    self.token_url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                response.raise_for_status()
                
                token_data = response.json()
                self.access_token = token_data["access_token"]
                
                # Calculate expiration time
                expires_in = token_data.get("expires_in", 3600)
                self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                
                logger.info("OAuth2 token refreshed successfully")
                
        except Exception as e:
            logger.error(f"Failed to fetch OAuth2 token: {e}")
            raise


class CustomHeaderAuth(AuthStrategy):
    """Custom header-based authentication."""
    
    def __init__(self, headers: Dict[str, str]):
        """
        Initialize custom header authentication.
        
        Args:
            headers: Dictionary of custom headers for authentication
        """
        self.custom_headers = headers
    
    async def apply_auth(self, request: httpx.Request) -> None:
        """Apply custom headers to request."""
        for key, value in self.custom_headers.items():
            request.headers[key] = value
    
    async def refresh_if_needed(self) -> None:
        """No refresh needed for custom headers."""
        pass


class DigestAuth(AuthStrategy):
    """HTTP Digest authentication."""
    
    def __init__(self, username: str, password: str):
        """
        Initialize digest authentication.
        
        Args:
            username: Username
            password: Password
        """
        self.username = username
        self.password = password
        self.auth = httpx.DigestAuth(username, password)
    
    async def apply_auth(self, request: httpx.Request) -> None:
        """
        Apply digest authentication to request.
        
        Note: Digest auth requires a challenge-response, so this is handled
        by httpx automatically when you use auth parameter.
        """
        # Digest auth is handled by httpx.DigestAuth automatically
        pass
    
    async def refresh_if_needed(self) -> None:
        """No refresh needed for digest auth."""
        pass
