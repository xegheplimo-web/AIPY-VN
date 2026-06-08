"""
Per-user rate limiting middleware
"""

import logging
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)

# Create limiter instance
limiter = Limiter(key_func=get_remote_address)


def get_user_id(request: Request) -> str:
    """
    Get user ID from request for rate limiting
    
    Priority:
    1. User ID from JWT token
    2. IP address as fallback
    """
    # Try to get user_id from JWT token
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            from src.services.ecc import get_jwt_service
            token = auth_header.split(" ")[1]
            payload = get_jwt_service().decode_token(token)
            user_id = payload.get("sub")
            if user_id:
                return f"user:{user_id}"
        except Exception:
            pass
    
    # Fallback to IP address
    return f"ip:{get_remote_address(request)}"


def per_user_rate_limit(limit: str):
    """
    Decorator for per-user rate limiting
    
    Args:
        limit: Rate limit string (e.g., "10/minute", "100/hour")
    """
    def decorator(func: Callable):
        async def wrapper(request: Request, *args, **kwargs):
            user_key = get_user_id(request)
            
            # Check rate limit
            try:
                limiter.check(limit, user_key)
            except RateLimitExceeded as e:
                logger.warning(f"Rate limit exceeded for {user_key}: {limit}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded: {limit}"
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


# Custom rate limit exceeded handler
async def custom_rate_limit_handler(request: Request, response: Response):
    """Custom handler for rate limit exceeded"""
    return Response(
        content='{"detail": "Rate limit exceeded. Please try again later."}',
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        media_type="application/json"
    )


# Apply custom handler
limiter._rate_limit_exceeded_handler = custom_rate_limit_handler
