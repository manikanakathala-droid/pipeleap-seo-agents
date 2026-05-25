"""
Rate limiting for API calls to prevent quota exhaustion.
Implements token bucket pattern with per-endpoint configuration.
"""

import logging
import time
from typing import Optional
from threading import Lock

log = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter for API endpoints.
    Prevents exceeding API quota limits.
    """
    
    def __init__(self, rate_per_second: float = 1.0, burst_size: int = 5):
        """
        Initialize rate limiter.
        
        Args:
            rate_per_second: Tokens generated per second (0.5 = 1 request per 2 seconds)
            burst_size: Maximum tokens to accumulate (burst capacity)
        """
        self.rate_per_second = rate_per_second
        self.burst_size = burst_size
        self.tokens = float(burst_size)
        self.last_update = time.time()
        self.lock = Lock()
    
    def allow(self, tokens_needed: int = 1) -> bool:
        """
        Check if request is allowed and consume tokens if yes.
        
        Args:
            tokens_needed: Number of tokens to consume
            
        Returns:
            True if request allowed, False if rate limited
        """
        with self.lock:
            self._refill()
            
            if self.tokens >= tokens_needed:
                self.tokens -= tokens_needed
                return True
            return False
    
    def wait_if_needed(self, tokens_needed: int = 1) -> float:
        """
        Block until tokens available, then consume them.
        
        Args:
            tokens_needed: Number of tokens to consume
            
        Returns:
            Time waited in seconds
        """
        start = time.time()
        
        while not self.allow(tokens_needed):
            time.sleep(0.01)  # Sleep briefly and retry
        
        waited = time.time() - start
        if waited > 0.1:
            log.debug(f"Rate limited: waited {waited:.2f}s for {tokens_needed} tokens")
        
        return waited
    
    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update
        tokens_generated = elapsed * self.rate_per_second
        
        self.tokens = min(self.burst_size, self.tokens + tokens_generated)
        self.last_update = now


class PerEndpointRateLimiter:
    """
    Manages rate limits for multiple API endpoints.
    Each endpoint has its own token bucket.
    """
    
    def __init__(self):
        self.limiters: dict[str, RateLimiter] = {}
        self.config = {}
        self.lock = Lock()
    
    def configure_endpoint(
        self,
        endpoint: str,
        rate_per_second: float = 1.0,
        burst_size: int = 5,
    ):
        """
        Configure rate limit for an endpoint.
        
        Args:
            endpoint: Endpoint identifier (e.g., "gsc_api", "github_api")
            rate_per_second: Tokens per second
            burst_size: Maximum burst size
        """
        with self.lock:
            self.config[endpoint] = {
                "rate_per_second": rate_per_second,
                "burst_size": burst_size,
            }
            self.limiters[endpoint] = RateLimiter(rate_per_second, burst_size)
    
    def allow(self, endpoint: str, tokens_needed: int = 1) -> bool:
        """Check if API call is allowed."""
        if endpoint not in self.limiters:
            self.configure_endpoint(endpoint)  # Use defaults
        
        return self.limiters[endpoint].allow(tokens_needed)
    
    def wait_if_needed(self, endpoint: str, tokens_needed: int = 1) -> float:
        """Wait until API call is allowed."""
        if endpoint not in self.limiters:
            self.configure_endpoint(endpoint)
        
        return self.limiters[endpoint].wait_if_needed(tokens_needed)


# Global rate limiter instance
_rate_limiter = PerEndpointRateLimiter()

# Configure common API endpoints with realistic rate limits
_rate_limiter.configure_endpoint("gsc_api", rate_per_second=0.5, burst_size=3)      # 30 req/min
_rate_limiter.configure_endpoint("ga4_api", rate_per_second=1.0, burst_size=5)      # 60 req/min
_rate_limiter.configure_endpoint("github_api", rate_per_second=0.3, burst_size=2)   # 18 req/min
_rate_limiter.configure_endpoint("pagespeed_api", rate_per_second=0.2, burst_size=1) # 12 req/min
_rate_limiter.configure_endpoint("indexing_api", rate_per_second=0.5, burst_size=3) # 30 req/min
_rate_limiter.configure_endpoint("crawler", rate_per_second=2.0, burst_size=5)      # 120 req/min


def get_rate_limiter() -> PerEndpointRateLimiter:
    """Get the global rate limiter instance."""
    return _rate_limiter


def rate_limit(endpoint: str, tokens: int = 1):
    """
    Decorator for rate-limiting function calls to a specific endpoint.
    
    Usage:
        @rate_limit("gsc_api")
        def fetch_search_analytics():
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            _rate_limiter.wait_if_needed(endpoint, tokens)
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Pre-configured decorators for common endpoints
gsc_rate_limit = rate_limit("gsc_api")
ga4_rate_limit = rate_limit("ga4_api")
github_rate_limit = rate_limit("github_api")
pagespeed_rate_limit = rate_limit("pagespeed_api")
indexing_rate_limit = rate_limit("indexing_api")
crawler_rate_limit = rate_limit("crawler")
