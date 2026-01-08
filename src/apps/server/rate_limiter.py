"""
Rate limiting middleware for API protection.
Implements a sliding window rate limiter with configurable limits.
"""

import time
import threading
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple
import logging

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_minute: int = 60
    requests_per_second: int = 10
    burst_size: int = 20
    enable_headers: bool = True


class SlidingWindowLimiter:
    """
    Sliding window rate limiter implementation.
    Tracks requests per client within a time window.
    """

    def __init__(
        self,
        requests_per_window: int = 60,
        window_size: float = 60.0
    ):
        """
        Initialize the rate limiter.

        :param requests_per_window: Maximum requests allowed per window
        :param window_size: Window size in seconds
        """
        self._requests_per_window = requests_per_window
        self._window_size = window_size
        self._client_data: Dict[str, list] = defaultdict(list)
        self._lock = threading.RLock()

    def is_allowed(self, client_id: str) -> Tuple[bool, int, float]:
        """
        Check if a request from the client is allowed.

        :param client_id: Unique identifier for the client
        :return: Tuple of (allowed, remaining_requests, reset_time)
        """
        current_time = time.time()
        window_start = current_time - self._window_size

        with self._lock:
            # Remove old requests outside the window
            self._client_data[client_id] = [
                req_time for req_time in self._client_data[client_id]
                if req_time > window_start
            ]

            current_requests = len(self._client_data[client_id])
            remaining = max(0, self._requests_per_window - current_requests)

            if current_requests >= self._requests_per_window:
                # Calculate reset time based on oldest request
                if self._client_data[client_id]:
                    oldest_request = min(self._client_data[client_id])
                    reset_time = oldest_request + self._window_size
                else:
                    reset_time = current_time + self._window_size
                return False, 0, reset_time

            # Record this request
            self._client_data[client_id].append(current_time)
            return True, remaining - 1, current_time + self._window_size

    def get_stats(self) -> Dict[str, int]:
        """
        Get rate limiter statistics.

        :return: Dictionary with stats
        """
        with self._lock:
            return {
                "active_clients": len(self._client_data),
                "requests_per_window": self._requests_per_window,
                "window_size_seconds": self._window_size
            }

    def clear(self) -> None:
        """Clear all rate limiting data."""
        with self._lock:
            self._client_data.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.
    Applies rate limits based on client IP address.
    """

    # Paths that are exempt from rate limiting
    EXEMPT_PATHS = {"/health", "/api/status", "/docs", "/redoc", "/openapi.json"}

    def __init__(
        self,
        app,
        config: Optional[RateLimitConfig] = None
    ):
        """
        Initialize the rate limit middleware.

        :param app: FastAPI application
        :param config: Rate limit configuration
        """
        super().__init__(app)
        self.config = config or RateLimitConfig()
        self._limiter = SlidingWindowLimiter(
            requests_per_window=self.config.requests_per_minute,
            window_size=60.0
        )

    async def dispatch(
        self, 
        request: Request, 
        call_next: Callable
    ) -> Response:
        """
        Process the request and apply rate limiting.

        :param request: The incoming request
        :param call_next: The next middleware or route handler
        :return: The response
        """
        # Skip rate limiting for exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Get client identifier (IP address)
        client_id = self._get_client_id(request)

        # Check rate limit
        allowed, remaining, reset_time = self._limiter.is_allowed(client_id)

        if not allowed:
            logger.warning(f"Rate limit exceeded for client: {client_id}")
            response = JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": round(reset_time - time.time())
                }
            )
            if self.config.enable_headers:
                response.headers["X-RateLimit-Limit"] = str(
                    self.config.requests_per_minute
                )
                response.headers["X-RateLimit-Remaining"] = "0"
                response.headers["X-RateLimit-Reset"] = str(int(reset_time))
                response.headers["Retry-After"] = str(
                    int(reset_time - time.time())
                )
            return response

        # Process the request
        response = await call_next(request)

        # Add rate limit headers to response
        if self.config.enable_headers:
            response.headers["X-RateLimit-Limit"] = str(
                self.config.requests_per_minute
            )
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(reset_time))

        return response

    def _get_client_id(self, request: Request) -> str:
        """
        Extract client identifier from request.
        Uses X-Forwarded-For header if present, otherwise client IP.

        :param request: The request object
        :return: Client identifier string
        """
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Get the first IP in the chain
            return forwarded_for.split(",")[0].strip()

        if request.client:
            return request.client.host

        return "unknown"

    def get_limiter_stats(self) -> Dict[str, int]:
        """Get rate limiter statistics."""
        return self._limiter.get_stats()
