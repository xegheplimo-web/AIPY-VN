import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all incoming requests with timing and request ID."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        start_time = time.time()
        method = request.method
        path = request.url.path

        response = await call_next(request)
        duration = (time.time() - start_time) * 1000

        print(f"[{request_id}] {method} {path} - {response.status_code} - {duration:.1f}ms")

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration:.1f}ms"
        return response
