"""
Request validation middleware.

Validates incoming requests for security and data integrity.
"""

import json
import logging
from typing import Callable
from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for validating incoming requests."""

    # Maximum request sizes
    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_JSON_SIZE = 1 * 1024 * 1024  # 1MB

    # Blocked user agents
    BLOCKED_USER_AGENTS = [
        "curl",
        "wget",
        "python-requests",
    ]

    async def dispatch(self, request: Request, call_next: Callable):
        """Validate request before processing."""
        
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.MAX_REQUEST_SIZE:
                    logger.warning(f"Request too large: {size} bytes from {request.client.host}")
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "error": "Request Too Large",
                            "message": f"Maximum request size is {self.MAX_REQUEST_SIZE / 1024 / 1024}MB",
                        },
                    )
            except ValueError:
                pass

        # Check user agent for scraping bots
        user_agent = request.headers.get("user-agent", "")
        if any(bot in user_agent.lower() for bot in self.BLOCKED_USER_AGENTS):
            # Only block for non-health endpoints
            if request.url.path not in ["/health", "/docs", "/openapi.json"]:
                logger.warning(f"Blocked user agent: {user_agent} from {request.client.host}")
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "error": "Forbidden",
                        "message": "Automated requests are not allowed",
                    },
                )

        # Validate JSON content type
        if request.headers.get("content-type") == "application/json":
            try:
                body = await request.body()
                if len(body) > self.MAX_JSON_SIZE:
                    logger.warning(f"JSON too large: {len(body)} bytes")
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "error": "Request Too Large",
                            "message": f"Maximum JSON size is {self.MAX_JSON_SIZE / 1024 / 1024}MB",
                        },
                    )
                
                # Validate JSON is parseable
                if body:
                    json.loads(body)
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON: {e}")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "error": "Invalid JSON",
                        "message": "Request body contains invalid JSON",
                    },
                )

        # Check for suspicious headers
        suspicious_headers = ["x-forwarded-for", "x-real-ip"]
        for header in suspicious_headers:
            if header in request.headers:
                # Log but don't block - could be legitimate proxy
                logger.debug(f"Suspicious header detected: {header}")

        response = await call_next(request)
        return response
