"""Decorators for auto-caching geocoding calls."""
from __future__ import annotations
import functools, logging, time
from typing import Awaitable, Callable
from src.services.geo_memory import get_geo_memory

logger = logging.getLogger(__name__)

def auto_cache_geo(api_name: str = "custom"):
    """Decorator: automatically cache geocoding results in L2 (SQLite)."""
    def decorator(func: Callable[..., Awaitable[dict]]) -> Callable[..., Awaitable[dict]]:
        @functools.wraps(func)
        async def wrapper(address: str, *args, **kwargs) -> dict:
            memory = get_geo_memory()
            force_refresh = kwargs.pop("force_refresh", False)
            if not force_refresh:
                cached = memory.lookup(address)
                if cached:
                    memory.log_api_call(api_name, address, True)
                    return {"latitude": cached["latitude"], "longitude": cached["longitude"], "address": cached["address_original"], "source": "memory", "access_count": cached.get("access_count", 1)}
            t0 = time.perf_counter()
            try:
                result = await func(address, *args, **kwargs)
                elapsed = (time.perf_counter() - t0) * 1000
                if result and "latitude" in result and "longitude" in result:
                    memory.save(address=address, latitude=result["latitude"], longitude=result["longitude"], full_response=result.get("raw"), source_api=api_name, metadata=result.get("metadata"))
                memory.log_api_call(api_name, address, False, response_time_ms=elapsed)
                result["source"] = f"api:{api_name}"
                return result
            except Exception as e:
                elapsed = (time.perf_counter() - t0) * 1000
                memory.log_api_call(api_name, address, False, response_time_ms=elapsed, success=False, error=str(e))
                raise
        return wrapper
    return decorator
