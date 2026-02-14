"""
Retry Policies

Provides retry logic with exponential backoff for HTTP requests.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional, Set
import random

import httpx

logger = logging.getLogger(__name__)


class RetryPolicy(ABC):
    """Base class for retry policies."""
    
    @abstractmethod
    async def should_retry(
        self,
        attempt: int,
        exception: Optional[Exception] = None,
        response: Optional[httpx.Response] = None
    ) -> bool:
        """
        Determine if request should be retried.
        
        Args:
            attempt: Current attempt number (0-indexed)
            exception: Exception that occurred (if any)
            response: HTTP response (if any)
            
        Returns:
            True if should retry, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_wait_time(self, attempt: int) -> float:
        """
        Get wait time before next retry.
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            Wait time in seconds
        """
        pass


class ExponentialBackoff(RetryPolicy):
    """Exponential backoff retry policy."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_status_codes: Optional[Set[int]] = None,
        retryable_exceptions: Optional[Set[type]] = None
    ):
        """
        Initialize exponential backoff retry policy.
        
        Args:
            max_retries: Maximum number of retries
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential calculation
            jitter: Add random jitter to prevent thundering herd
            retryable_status_codes: HTTP status codes that should trigger retry
            retryable_exceptions: Exception types that should trigger retry
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        
        # Default retryable status codes (5xx and select 4xx)
        self.retryable_status_codes = retryable_status_codes or {
            408,  # Request Timeout
            429,  # Too Many Requests
            500,  # Internal Server Error
            502,  # Bad Gateway
            503,  # Service Unavailable
            504,  # Gateway Timeout
        }
        
        # Default retryable exceptions
        self.retryable_exceptions = retryable_exceptions or {
            httpx.ConnectError,
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
            httpx.WriteTimeout,
            httpx.PoolTimeout,
            httpx.NetworkError,
        }
    
    async def should_retry(
        self,
        attempt: int,
        exception: Optional[Exception] = None,
        response: Optional[httpx.Response] = None
    ) -> bool:
        """Determine if request should be retried."""
        # Check max retries
        if attempt >= self.max_retries:
            return False
        
        # Check exception
        if exception:
            return any(
                isinstance(exception, exc_type)
                for exc_type in self.retryable_exceptions
            )
        
        # Check response status code
        if response:
            return response.status_code in self.retryable_status_codes
        
        return False
    
    async def get_wait_time(self, attempt: int) -> float:
        """Calculate wait time with exponential backoff and jitter."""
        # Calculate exponential delay
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        
        # Add jitter (random value between 0 and delay)
        if self.jitter:
            delay = random.uniform(0, delay)
        
        return delay


class FixedRetry(RetryPolicy):
    """Fixed delay retry policy."""
    
    def __init__(
        self,
        max_retries: int = 3,
        delay: float = 1.0,
        retryable_status_codes: Optional[Set[int]] = None,
        retryable_exceptions: Optional[Set[type]] = None
    ):
        """
        Initialize fixed delay retry policy.
        
        Args:
            max_retries: Maximum number of retries
            delay: Fixed delay between retries in seconds
            retryable_status_codes: HTTP status codes that should trigger retry
            retryable_exceptions: Exception types that should trigger retry
        """
        self.max_retries = max_retries
        self.delay = delay
        
        self.retryable_status_codes = retryable_status_codes or {
            408, 429, 500, 502, 503, 504
        }
        
        self.retryable_exceptions = retryable_exceptions or {
            httpx.ConnectError,
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
            httpx.WriteTimeout,
        }
    
    async def should_retry(
        self,
        attempt: int,
        exception: Optional[Exception] = None,
        response: Optional[httpx.Response] = None
    ) -> bool:
        """Determine if request should be retried."""
        if attempt >= self.max_retries:
            return False
        
        if exception:
            return any(
                isinstance(exception, exc_type)
                for exc_type in self.retryable_exceptions
            )
        
        if response:
            return response.status_code in self.retryable_status_codes
        
        return False
    
    async def get_wait_time(self, attempt: int) -> float:
        """Return fixed delay."""
        return self.delay


class NoRetry(RetryPolicy):
    """No retry policy."""
    
    async def should_retry(
        self,
        attempt: int,
        exception: Optional[Exception] = None,
        response: Optional[httpx.Response] = None
    ) -> bool:
        """Never retry."""
        return False
    
    async def get_wait_time(self, attempt: int) -> float:
        """No wait time."""
        return 0.0
