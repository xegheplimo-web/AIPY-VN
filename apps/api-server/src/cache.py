"""Redis cache integration for VietStore RAG.

Provides caching for expensive operations:
- Store search results
- Product lookups
- Shipping calculations
- Suggestions
- User sessions
- API responses
"""

import json
import os
import logging
from typing import Any, List, Optional

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Redis client (install via: uv add redis)
try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class CacheClient:
    """Redis cache client with JSON serialization and advanced features."""

    def __init__(self):
        self.client = None
        self._default_ttl = 3600  # 1 hour default
        self._init_client()

    def _init_client(self):
        if not REDIS_AVAILABLE:
            logger.warning("redis not installed. Cache disabled.")
            return
        try:
            self.client = redis.from_url(
                REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info("Redis cache connected.")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}")
            self.client = None

    async def connect(self):
        """Explicitly connect to Redis (for async initialization)"""
        if not REDIS_AVAILABLE or self.client:
            return
        try:
            self.client = redis.from_url(
                REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            await self.client.ping()
            logger.info("Redis cache connected.")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}")
            self.client = None

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.client:
            await self.client.close()
            self.client = None
            logger.info("Redis cache disconnected.")

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        if not self.client:
            return None
        try:
            value = await self.client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        return None

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set value in cache with expiration (seconds)."""
        if not self.client:
            return False
        try:
            if not isinstance(value, str):
                value = json.dumps(value)
            ttl = expire or self._default_ttl
            await self.client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.client:
            return False
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
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
            logger.error(f"Cache invalidate error: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.client:
            return False
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for a key."""
        if not self.client:
            return False
        try:
            return await self.client.expire(key, ttl)
        except Exception as e:
            logger.error(f"Cache expire error: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """Get remaining time to live for a key."""
        if not self.client:
            return -2
        try:
            return await self.client.ttl(key)
        except Exception as e:
            logger.error(f"Cache TTL error: {e}")
            return -2

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a counter in cache."""
        if not self.client:
            return 0
        try:
            return await self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error: {e}")
            return 0

    async def get_many(self, keys: List[str]) -> dict:
        """Get multiple values from cache."""
        if not self.client:
            return {}
        try:
            values = await self.client.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        result[key] = value
            return result
        except Exception as e:
            logger.error(f"Cache get_many error: {e}")
            return {}

    async def set_many(self, mapping: dict, ttl: Optional[int] = None) -> bool:
        """Set multiple values in cache."""
        if not self.client:
            return False
        try:
            ttl = ttl or self._default_ttl
            pipe = self.client.pipeline()
            for key, value in mapping.items():
                if not isinstance(value, str):
                    value = json.dumps(value)
                pipe.setex(key, ttl, value)
            await pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Cache set_many error: {e}")
            return False

    async def clear(self) -> bool:
        """Clear all cached data (use with caution!)."""
        if not self.client:
            return False
        try:
            await self.client.flushdb()
            logger.warning("Cache cleared")
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False

    async def get_stats(self) -> dict:
        """Get cache statistics."""
        if not self.client:
            return {"connected": False}
        try:
            info = await self.client.info()
            return {
                "connected": True,
                "used_memory": info.get("used_memory_human"),
                "total_keys": info.get("db0", {}).get("keys"),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"connected": False, "error": str(e)}


# Singleton instance
cache = CacheClient()
