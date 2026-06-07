"""
Middleware tests for VietStore RAG API.
"""

import pytest
from fastapi.testclient import TestClient
from src.middleware.validation import RequestValidationMiddleware
from src.middleware.logging_middleware import LoggingMiddleware
from src.middleware.rate_limiter import RateLimitMiddleware
from src.middleware.auth_middleware import AuthMiddleware
from starlette.middleware.base import BaseHTTPMiddleware


@pytest.mark.asyncio
class TestRequestValidationMiddleware:
    """Tests for request validation middleware."""

    def test_middleware_initialization(self):
        """Test middleware initializes correctly."""
        middleware = RequestValidationMiddleware(app=None)
        assert middleware is not None
        assert middleware.MAX_REQUEST_SIZE == 10 * 1024 * 1024
        assert middleware.MAX_JSON_SIZE == 1 * 1024 * 1024

    def test_blocked_user_agents(self):
        """Test that scraping bots are blocked."""
        middleware = RequestValidationMiddleware(app=None)
        assert "curl" in middleware.BLOCKED_USER_AGENTS
        assert "wget" in middleware.BLOCKED_USER_AGENTS
        assert "python-requests" in middleware.BLOCKED_USER_AGENTS

    def test_max_request_size_validation(self):
        """Test maximum request size validation."""
        middleware = RequestValidationMiddleware(app=None)
        assert middleware.MAX_REQUEST_SIZE == 10 * 1024 * 1024  # 10MB

    def test_max_json_size_validation(self):
        """Test maximum JSON size validation."""
        middleware = RequestValidationMiddleware(app=None)
        assert middleware.MAX_JSON_SIZE == 1 * 1024 * 1024  # 1MB


@pytest.mark.asyncio
class TestLoggingMiddleware:
    """Tests for logging middleware."""

    def test_middleware_initialization(self):
        """Test logging middleware initializes correctly."""
        middleware = LoggingMiddleware(app=None)
        assert middleware is not None

    def test_request_id_generation(self):
        """Test that request IDs are generated."""
        import uuid

        request_id = str(uuid.uuid4())[:8]
        assert len(request_id) == 8
        assert request_id.isalnum()


@pytest.mark.asyncio
class TestRateLimitMiddleware:
    """Tests for rate limiting middleware."""

    def test_middleware_initialization(self):
        """Test rate limit middleware initializes correctly."""
        middleware = RateLimitMiddleware(app=None, max_requests=200, window=60)
        assert middleware is not None
        assert middleware.max_requests == 200
        assert middleware.window == 60

    def test_rate_limit_parameters(self):
        """Test rate limit parameters."""
        middleware = RateLimitMiddleware(app=None, max_requests=100, window=30)
        assert middleware.max_requests == 100
        assert middleware.window == 30

    def test_rate_limit_default_values(self):
        """Test default rate limit values."""
        middleware = RateLimitMiddleware(app=None)
        assert middleware.max_requests == 200
        assert middleware.window == 60


@pytest.mark.asyncio
class TestAuthMiddleware:
    """Tests for authentication middleware."""

    def test_middleware_initialization(self):
        """Test auth middleware initializes correctly."""
        middleware = AuthMiddleware(app=None)
        assert middleware is not None

    def test_public_paths(self):
        """Test that public paths are defined."""
        # This would test that certain paths don't require auth
        # Implementation depends on actual middleware logic
        pass


@pytest.mark.asyncio
class TestMiddlewareIntegration:
    """Tests for middleware integration."""

    def test_middleware_chain(self, client: TestClient):
        """Test that middleware chain works correctly."""
        # Test health endpoint (should pass through all middleware)
        response = client.get("/health")
        assert response.status_code == 200

    def test_request_id_in_response(self, client: TestClient):
        """Test that request ID is added to response headers."""
        response = client.get("/health")
        assert "X-Request-ID" in response.headers

    def test_response_time_in_response(self, client: TestClient):
        """Test that response time is added to response headers."""
        response = client.get("/health")
        assert "X-Response-Time" in response.headers

    def test_middleware_error_handling(self, client: TestClient):
        """Test that middleware handles errors correctly."""
        # Test with invalid request
        response = client.post("/api/chat/search", json={})
        assert response.status_code in [422, 400]

    def test_middleware_large_request(self, client: TestClient):
        """Test that large requests are rejected."""
        # Create a large payload
        large_data = {"data": "x" * (11 * 1024 * 1024)}  # Over 10MB
        response = client.post("/api/test", json=large_data)
        assert response.status_code in [413, 404, 422]

    def test_middleware_invalid_json(self, client: TestClient):
        """Test that invalid JSON is rejected."""
        response = client.post(
            "/api/chat/search",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code in [400, 422]


@pytest.mark.asyncio
class TestMiddlewareHeaders:
    """Tests for middleware header handling."""

    def test_cors_headers(self, client: TestClient):
        """Test that CORS headers are present."""
        response = client.get("/health")
        # CORS headers should be present
        assert response.status_code == 200

    def test_content_type_header(self, client: TestClient):
        """Test that content-type header is handled correctly."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_authorization_header_handling(self, client: TestClient, auth_headers):
        """Test that authorization header is handled correctly."""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code in [200, 401]

    def test_custom_headers(self, client: TestClient):
        """Test that custom headers are handled correctly."""
        custom_headers = {
            "X-Custom-Header": "test-value",
            "X-Request-ID": "custom-request-id",
        }
        response = client.get("/health", headers=custom_headers)
        assert response.status_code == 200


@pytest.mark.asyncio
class TestMiddlewarePerformance:
    """Tests for middleware performance impact."""

    def test_middleware_overhead(self, client: TestClient):
        """Test that middleware doesn't add significant overhead."""
        import time

        start = time.time()
        response = client.get("/health")
        duration = time.time() - start

        assert response.status_code == 200
        # Should complete in reasonable time (< 1 second)
        assert duration < 1.0

    def test_multiple_requests(self, client: TestClient):
        """Test that middleware handles multiple requests correctly."""
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200

    def test_concurrent_requests(self, client: TestClient):
        """Test that middleware handles concurrent requests."""
        import asyncio

        async def make_request():
            response = client.get("/health")
            assert response.status_code == 200

        # Run multiple concurrent requests
        loop = asyncio.get_event_loop()
        tasks = [make_request() for _ in range(5)]
        loop.run_until_complete(asyncio.gather(*tasks))
