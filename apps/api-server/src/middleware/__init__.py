"""Production middleware for VietStore RAG API."""

from .logging_middleware import LoggingMiddleware
from .error_handler import setup_error_handlers
from .rate_limiter import RateLimitMiddleware
from .auth_middleware import (
    AuthMiddleware,
    get_current_user,
    require_auth,
    require_admin,
    require_owner_or_admin,
)
from .validation import RequestValidationMiddleware
from .csrf import CSRFMiddleware
from .body_size import BodySizeLimitMiddleware

__all__ = [
    "LoggingMiddleware",
    "setup_error_handlers",
    "RateLimitMiddleware",
    "AuthMiddleware",
    "get_current_user",
    "require_auth",
    "require_admin",
    "require_owner_or_admin",
    "RequestValidationMiddleware",
    "CSRFMiddleware",
    "BodySizeLimitMiddleware",
]
