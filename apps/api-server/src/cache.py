"""Redis cache integration for VietStore RAG.

Provides caching for expensive operations:
- Store search results
- Product lookups
- Shipping calculations
- Suggestions
"""

import os
import json
from typing import Optional, Any

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Redis client (install via: uv add redis)
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class CacheClient:
    """Redis cache client with JSON serialization."""

    def __init__(self):
        self.client = None
        self._init_client()

    def _init_client(self):
        if not REDIS_AVAILABLE:
            print("WARNING: redis not installed. Cache disabled.")
            return
        try:
            self.client = redis.from_url(REDIS_URL, decode_responses=True)
            print("Redis cache connected.")
        except Exception as e:
            print(f"WARNING: Could not connect to Redis: {e}")
            self.client = None

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.client:
            return None
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            print(f"Cache get error: {e}")
        return None

    async def set(self, key: str, value: Any, expire: int = 300) -> bool:
        """Set value in cache with expiration (seconds)."""
        if not self.client:
            return False
        try:
            await self.client.setex(key, expire, json.dumps(value))
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.client:
            return False
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        if not self.client:
            return 0
        try:
            keys = await self.client.keys(pattern)
            if keys:
                await self.client.delete(*keys)
            return len(keys)
        except Exception as e:
            print(f"Cache invalidate error: {e}")
            return 0


# Singleton instance
cache = CacheClient()
