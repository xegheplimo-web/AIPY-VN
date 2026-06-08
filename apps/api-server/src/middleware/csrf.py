"""
CSRF Protection Middleware

Provides CSRF protection for state-changing requests.
"""

import hashlib
import logging
import secrets

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class CSRFMiddleware(BaseHTTPMiddleware):
    """Middleware for CSRF protection."""

    # Methods that require CSRF protection
    PROTECTED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    # Paths that don't require CSRF protection
    EXEMPT_PATHS = {
        "/health",
        "/docs",
        "/openapi.json",
        "/api/auth/public-key",
        "/api/auth/register",
        "/api/auth/login",
        "/api/chat/search",
        "/api/suggestions",
        "/api/stores",
        "/api/products",
    }

    def __init__(self, app, secret_key: str | None = None):
        super().__init__(app)
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        logger.info("CSRF middleware initialized")

    async def dispatch(self, request: Request, call_next):
        """Process request and validate CSRF token for protected methods."""
        # Skip CSRF for exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Skip for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Only protect state-changing methods
        if request.method not in self.PROTECTED_METHODS:
            return await call_next(request)

        # Get CSRF token from headers
        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "CSRF token missing"},
            )

        # Validate CSRF token
        if not self._validate_token(request, csrf_token):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Invalid CSRF token"},
            )

        return await call_next(request)

    def _validate_token(self, request: Request, token: str) -> bool:
        """
        Validate CSRF token.

        Args:
            request: FastAPI request
            token: CSRF token from headers

        Returns:
            True if token is valid
        """
        try:
            # In a real implementation, you would:
            # 1. Check if token exists in session
            # 2. Verify token matches expected value
            # 3. Check token hasn't expired

            # For now, we'll use a simple validation
            # In production, implement proper session-based CSRF tokens
            expected_token = self._generate_token(request)
            return secrets.compare_digest(token, expected_token)
        except Exception as e:
            logger.error(f"CSRF token validation error: {e}", exc_info=True)
            return False

    def _generate_token(self, request: Request) -> str:
        """
        Generate CSRF token for request.

        Args:
            request: FastAPI request

        Returns:
            CSRF token
        """
        # In production, this should be session-based
        # For now, use a simple hash-based token
        data = f"{request.url.path}:{request.client.host if request.client else 'unknown'}"
        return hashlib.sha256(f"{data}{self.secret_key}".encode()).hexdigest()
