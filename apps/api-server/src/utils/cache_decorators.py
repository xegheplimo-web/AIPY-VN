"""
Caching decorators for API endpoints
"""

import functools
import logging
from typing import Callable, Optional, Any
from src.cache import cache

logger = logging.getLogger(__name__)


def cache_result(ttl: int = 3600, key_prefix: str = ""):
    """
    Decorator to cache function results
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
    
    Usage:
        @cache_result(ttl=300, key_prefix="product")
        async def get_product(product_id: str):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached = await cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache.set(cache_key, result, ttl)
            logger.debug(f"Cache miss for key: {cache_key}")
            
            return result
        
        return wrapper
    return decorator


def cache_by_user(ttl: int = 1800):
    """
    Decorator to cache function results per user
    
    Args:
        ttl: Time to live in seconds
    
    Usage:
        @cache_by_user(ttl=300)
        async def get_user_orders(user_id: str):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user_id from kwargs or args
            user_id = kwargs.get("user_id") or (args[0] if args else None)
            
            if not user_id:
                return await func(*args, **kwargs)
            
            # Generate cache key
            key_parts = ["user", str(user_id), func.__name__]
            key_parts.extend(str(arg) for arg in args[1:])
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached = await cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for user key: {cache_key}")
                return cached
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache.set(cache_key, result, ttl)
            logger.debug(f"Cache miss for user key: {cache_key}")
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    """
    Decorator to invalidate cache after function execution
    
    Args:
        pattern: Cache key pattern to invalidate
    
    Usage:
        @invalidate_cache("product:*")
        async def update_product(product_id: str, data: dict):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Execute function
            result = await func(*args, **kwargs)
            
            # Invalidate cache
            count = await cache.invalidate_pattern(pattern)
            logger.info(f"Invalidated {count} cache keys matching pattern: {pattern}")
            
            return result
        
        return wrapper
    return decorator


def cache_response(ttl: int = 300):
    """
    Decorator for FastAPI endpoints to cache responses
    
    Args:
        ttl: Time to live in seconds
    
    Usage:
        @app.get("/products/{id}")
        @cache_response(ttl=300)
        async def get_product(id: str):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from args (FastAPI passes request as first arg)
            request = None
            for arg in args:
                if hasattr(arg, 'url'):
                    request = arg
                    break
            
            if not request:
                return await func(*args, **kwargs)
            
            # Generate cache key from URL
            cache_key = f"response:{request.url.path}:{request.url.query}"
            
            # Try to get from cache
            cached = await cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for response: {cache_key}")
                return cached
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache.set(cache_key, result, ttl)
            logger.debug(f"Cache miss for response: {cache_key}")
            
            return result
        
        return wrapper
    return decorator
