"""Tests for the rate limiter module."""
import sys
import time

sys.path.append(".")

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.apps.server.rate_limiter import (
    RateLimitMiddleware, 
    RateLimitConfig,
    SlidingWindowLimiter
)


class TestSlidingWindowLimiter:
    """Test suite for SlidingWindowLimiter class."""

    def test_allows_requests_within_limit(self):
        """Test that requests within limit are allowed."""
        limiter = SlidingWindowLimiter(
            requests_per_window=10,
            window_size=60.0
        )
        
        for _ in range(10):
            allowed, remaining, _ = limiter.is_allowed("client1")
            assert allowed is True

    def test_blocks_requests_over_limit(self):
        """Test that requests over limit are blocked."""
        limiter = SlidingWindowLimiter(
            requests_per_window=3,
            window_size=60.0
        )
        
        # First 3 should be allowed
        for _ in range(3):
            allowed, _, _ = limiter.is_allowed("client1")
            assert allowed is True
        
        # 4th should be blocked
        allowed, remaining, _ = limiter.is_allowed("client1")
        assert allowed is False
        assert remaining == 0

    def test_different_clients_have_separate_limits(self):
        """Test that different clients have independent limits."""
        limiter = SlidingWindowLimiter(
            requests_per_window=2,
            window_size=60.0
        )
        
        # Client1 uses their limit
        limiter.is_allowed("client1")
        limiter.is_allowed("client1")
        allowed1, _, _ = limiter.is_allowed("client1")
        
        # Client2 should still be able to make requests
        allowed2, _, _ = limiter.is_allowed("client2")
        
        assert allowed1 is False
        assert allowed2 is True

    def test_remaining_count_decreases(self):
        """Test that remaining count decreases correctly."""
        limiter = SlidingWindowLimiter(
            requests_per_window=5,
            window_size=60.0
        )
        
        _, remaining1, _ = limiter.is_allowed("client1")
        _, remaining2, _ = limiter.is_allowed("client1")
        
        assert remaining1 == 4
        assert remaining2 == 3

    def test_window_expiration(self):
        """Test that old requests are removed from window."""
        limiter = SlidingWindowLimiter(
            requests_per_window=2,
            window_size=0.1  # 100ms window
        )
        
        # Use up the limit
        limiter.is_allowed("client1")
        limiter.is_allowed("client1")
        
        # Should be blocked now
        allowed, _, _ = limiter.is_allowed("client1")
        assert allowed is False
        
        # Wait for window to pass
        time.sleep(0.15)
        
        # Should be allowed again
        allowed, _, _ = limiter.is_allowed("client1")
        assert allowed is True

    def test_stats(self):
        """Test that stats are returned correctly."""
        limiter = SlidingWindowLimiter(
            requests_per_window=10,
            window_size=60.0
        )
        
        limiter.is_allowed("client1")
        limiter.is_allowed("client2")
        
        stats = limiter.get_stats()
        assert stats["active_clients"] == 2
        assert stats["requests_per_window"] == 10
        assert stats["window_size_seconds"] == 60.0

    def test_clear(self):
        """Test that clear removes all rate limiting data."""
        limiter = SlidingWindowLimiter(
            requests_per_window=2,
            window_size=60.0
        )
        
        limiter.is_allowed("client1")
        limiter.is_allowed("client1")
        
        # Should be blocked
        allowed, _, _ = limiter.is_allowed("client1")
        assert allowed is False
        
        # Clear and try again
        limiter.clear()
        allowed, _, _ = limiter.is_allowed("client1")
        assert allowed is True


class TestRateLimitMiddleware:
    """Test suite for RateLimitMiddleware."""

    def create_test_app(self, config: RateLimitConfig = None) -> FastAPI:
        """Create a test FastAPI app with rate limiting."""
        app = FastAPI()
        app.add_middleware(RateLimitMiddleware, config=config)
        
        @app.get("/test")
        def test_endpoint():
            return {"status": "ok"}
        
        @app.get("/health")
        def health_endpoint():
            return {"status": "healthy"}
        
        return app

    def test_allows_normal_requests(self):
        """Test that normal request rate is allowed."""
        config = RateLimitConfig(requests_per_minute=10)
        app = self.create_test_app(config)
        
        with TestClient(app) as client:
            response = client.get("/test")
            assert response.status_code == 200

    def test_blocks_excessive_requests(self):
        """Test that excessive requests are blocked."""
        config = RateLimitConfig(requests_per_minute=3)
        app = self.create_test_app(config)
        
        with TestClient(app) as client:
            # Make requests up to the limit
            for _ in range(3):
                response = client.get("/test")
                assert response.status_code == 200
            
            # Next request should be rate limited
            response = client.get("/test")
            assert response.status_code == 429
            assert response.json()["error"] == "rate_limit_exceeded"

    def test_exempt_paths_not_rate_limited(self):
        """Test that exempt paths are not rate limited."""
        config = RateLimitConfig(requests_per_minute=1)
        app = self.create_test_app(config)
        
        with TestClient(app) as client:
            # Health endpoint should always work
            for _ in range(10):
                response = client.get("/health")
                assert response.status_code == 200

    def test_rate_limit_headers(self):
        """Test that rate limit headers are included."""
        config = RateLimitConfig(
            requests_per_minute=10,
            enable_headers=True
        )
        app = self.create_test_app(config)
        
        with TestClient(app) as client:
            response = client.get("/test")
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers
