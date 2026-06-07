import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from src.cache import cache

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiter with Redis backing for production multi-instance support."""

    def __init__(self, app, max_requests: int = 200, window: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window
        self._requests = {}  # Fallback in-memory storage if Redis unavailable
        self.use_redis = cache.client is not None

        if self.use_redis:
            logger.info("Rate limiter using Redis backend")
        else:
            logger.warning(
                "Rate limiter using in-memory fallback (not suitable for production)"
            )

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path == "/health":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Use Redis if available, otherwise fallback to in-memory
        if self.use_redis:
            allowed, retry_after = await self._check_redis_rate_limit(client_ip, now)
        else:
            allowed, retry_after = self._check_memory_rate_limit(client_ip, now)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate Limit Exceeded",
                    "message": f"Too many requests. Limit: {self.max_requests}/{self.window}s",
                    "retry_after": retry_after,
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Window"] = str(self.window)
        return response

    async def _check_redis_rate_limit(
        self, client_ip: str, now: float
    ) -> tuple[bool, int]:
        """Check rate limit using Redis."""
        try:
            key = f"ratelimit:{client_ip}"
            pipe = cache.client.pipeline()

            # Get current count and expiry
            pipe.get(key)
            pipe.ttl(key)
            results = await pipe.execute()

            current_count = int(results[0]) if results[0] else 0
            ttl = results[1]

            if current_count >= self.max_requests:
                # Rate limit exceeded
                return False, ttl if ttl > 0 else self.window

            # Increment counter
            if ttl == -1 or ttl == -2:  # Key doesn't exist or no expiry
                # New window
                await cache.client.setex(key, self.window, 1)
            else:
                # Existing window, increment
                await cache.client.incr(key)

            return True, 0

        except Exception as e:
            logger.error(
                f"Redis rate limit check failed, falling back to in-memory: {e}",
                exc_info=True,
            )
            # Fallback to in-memory on Redis error
            return self._check_memory_rate_limit(client_ip, now)

    def _check_memory_rate_limit(self, client_ip: str, now: float) -> tuple[bool, int]:
        """Check rate limit using in-memory storage (fallback)."""
        # Clean old entries
        if client_ip in self._requests:
            self._requests[client_ip] = [
                (ts, cnt)
                for ts, cnt in self._requests[client_ip]
                if now - ts < self.window
            ]
        else:
            self._requests[client_ip] = []

        # Count requests in window
        total = sum(cnt for ts, cnt in self._requests[client_ip])

        if total >= self.max_requests:
            return False, self.window

        self._requests[client_ip].append((now, 1))
        return True, 0
