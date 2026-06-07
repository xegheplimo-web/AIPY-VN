import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter.

    TODO: Replace with Redis-backed rate limiter for production multi-instance.
    """

    def __init__(self, app, max_requests: int = 200, window: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window
        self._requests = {}  # {ip: [(timestamp, count)]}

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path == "/health":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

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
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate Limit Exceeded",
                    "message": f"Too many requests. Limit: {self.max_requests}/{self.window}s",
                    "retry_after": self.window,
                },
            )

        self._requests[client_ip].append((now, 1))

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Window"] = str(self.window)
        return response
