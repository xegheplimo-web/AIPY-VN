"""Production middleware for VietStore RAG API."""

from .auth_middleware import (
    AuthMiddleware,
    get_current_user,
    require_admin,
    require_auth,
    require_owner_or_admin,
)
from .body_size import BodySizeLimitMiddleware
from .csrf import CSRFMiddleware
from .error_handler import setup_error_handlers
from .logging_middleware import LoggingMiddleware
from .rate_limiter import RateLimitMiddleware
from .security_headers import SecurityHeadersMiddleware
from .validation import RequestValidationMiddleware

__all__ = [
    "AuthMiddleware",
    "BodySizeLimitMiddleware",
    "CSRFMiddleware",
    "LoggingMiddleware",
    "RateLimitMiddleware",
    "RequestValidationMiddleware",
    "SecurityHeadersMiddleware",
    "get_current_user",
    "require_admin",
    "require_auth",
    "require_owner_or_admin",
    "setup_error_handlers",
]
