"""
Request Body Size Limit Middleware

Protects against large request bodies that could cause memory issues.
"""

import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to limit request body size."""

    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_size = max_size
        logger.info(f"Body size limit middleware initialized with max size: {max_size} bytes")

    async def dispatch(self, request: Request, call_next):
        # Skip size check for GET, HEAD, OPTIONS
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return await call_next(request)

        # Check content-length header if present
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_size:
                    logger.warning(f"Request body too large: {size} bytes (max: {self.max_size})")
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": "Payload Too Large",
                            "message": f"Request body exceeds maximum size of {self.max_size} bytes",
                            "max_size": self.max_size,
                        },
                    )
            except ValueError:
                logger.warning("Invalid content-length header")

        response = await call_next(request)
        return response
