"""
Redis Cache Service for Geo Search

Caches geo search results, geocoding results, and frequently accessed data
to improve performance and reduce database load.
"""

import json
import logging
from typing import Any

from src.cache import cache

logger = logging.getLogger(__name__)


class GeoCacheService:
    """
    Redis caching service for geo search operations.
    
    Cache TTL:
    - Nearby search: 15 minutes
    - Full-text search: 10 minutes
    - Geocoding: 1 hour
    - Reverse geocoding: 1 hour
    - Categories: 1 hour
    - Brands: 1 hour
    - Autocomplete: 5 minutes
    """

    # Cache TTL in seconds
    TTL_NEARBY = 15 * 60  # 15 minutes
    TTL_SEARCH = 10 * 60  # 10 minutes
    TTL_GEOCODE = 60 * 60  # 1 hour
    TTL_REVERSE_GEOCODE = 60 * 60  # 1 hour
    TTL_CATEGORIES = 60 * 60  # 1 hour
    TTL_BRANDS = 60 * 60  # 1 hour
    TTL_AUTOCOMPLETE = 5 * 60  # 5 minutes

    def __init__(self):
        """Initialize cache service."""
        self.enabled = cache.client is not None
        if self.enabled:
            logger.info("✅ Redis cache service enabled")
        else:
            logger.warning("⚠️  Redis cache service disabled")

    def _make_key(self, prefix: str, *args) -> str:
        """Generate cache key."""
        parts = [prefix] + [str(arg) for arg in args]
        return ":".join(parts)

    async def get_nearby(
        self,
        lat: float,
        lng: float,
        radius_km: float,
        category: str | None = None,
        brand: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Get cached nearby search results.
        
        Args:
            lat: Latitude
            lng: Longitude
            radius_km: Search radius
            category: Optional category filter
            brand: Optional brand filter
            
        Returns:
            Cached results or None
        """
        if not self.enabled:
            return None

        key = self._make_key(
            "nearby",
            lat, lng, radius_km, category, brand
        )
        
        try:
            cached = await cache.client.get(key)
            if cached:
                logger.debug(f"Cache HIT: nearby {lat},{lng},{radius_km}")
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        
        return None

    async def set_nearby(
        self,
        lat: float,
        lng: float,
        radius_km: float,
        category: str | None,
        brand: str | None,
        results: dict[str, Any],
    ) -> bool:
        """
        Cache nearby search results.
        
        Args:
            lat: Latitude
            lng: Longitude
            radius_km: Search radius
            category: Optional category filter
            brand: Optional brand filter
            results: Search results to cache
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        key = self._make_key(
            "nearby",
            lat, lng, radius_km, category, brand
        )
        
        try:
            await cache.client.setex(
                key,
                self.TTL_NEARBY,
                json.dumps(results)
            )
            logger.debug(f"Cache SET: nearby {lat},{lng},{radius_km}")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def get_search(
        self,
        query: str,
        lat: float | None,
        lng: float | None,
        radius_km: float,
        category: str | None,
        brand: str | None,
    ) -> dict[str, Any] | None:
        """
        Get cached search results.
        
        Args:
            query: Search query
            lat: Optional latitude
            lng: Optional longitude
            radius_km: Search radius
            category: Optional category filter
            brand: Optional brand filter
            
        Returns:
            Cached results or None
        """
        if not self.enabled:
            return None

        key = self._make_key(
            "search",
            query, lat, lng, radius_km, category, brand
        )
        
        try:
            cached = await cache.client.get(key)
            if cached:
                logger.debug(f"Cache HIT: search {query}")
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        
        return None

    async def set_search(
        self,
        query: str,
        lat: float | None,
        lng: float | None,
        radius_km: float,
        category: str | None,
        brand: str | None,
        results: dict[str, Any],
    ) -> bool:
        """
        Cache search results.
        
        Args:
            query: Search query
            lat: Optional latitude
            lng: Optional longitude
            radius_km: Search radius
            category: Optional category filter
            brand: Optional brand filter
            results: Search results to cache
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        key = self._make_key(
            "search",
            query, lat, lng, radius_km, category, brand
        )
        
        try:
            await cache.client.setex(
                key,
                self.TTL_SEARCH,
                json.dumps(results)
            )
            logger.debug(f"Cache SET: search {query}")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def get_geocode(self, address: str) -> dict[str, Any] | None:
        """
        Get cached geocoding results.
        
        Args:
            address: Address to geocode
            
        Returns:
            Cached results or None
        """
        if not self.enabled:
            return None

        key = self._make_key("geocode", address.lower().strip())
        
        try:
            cached = await cache.client.get(key)
            if cached:
                logger.debug(f"Cache HIT: geocode {address}")
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        
        return None

    async def set_geocode(
        self,
        address: str,
        results: dict[str, Any],
    ) -> bool:
        """
        Cache geocoding results.
        
        Args:
            address: Address that was geocoded
            results: Geocoding results to cache
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        key = self._make_key("geocode", address.lower().strip())
        
        try:
            await cache.client.setex(
                key,
                self.TTL_GEOCODE,
                json.dumps(results)
            )
            logger.debug(f"Cache SET: geocode {address}")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def get_reverse_geocode(
        self,
        lat: float,
        lng: float,
    ) -> dict[str, Any] | None:
        """
        Get cached reverse geocoding results.
        
        Args:
            lat: Latitude
            lng: Longitude
            
        Returns:
            Cached results or None
        """
        if not self.enabled:
            return None

        # Round coordinates to reduce cache fragmentation
        lat_rounded = round(lat, 4)
        lng_rounded = round(lng, 4)
        key = self._make_key("reverse_geocode", lat_rounded, lng_rounded)
        
        try:
            cached = await cache.client.get(key)
            if cached:
                logger.debug(f"Cache HIT: reverse_geocode {lat},{lng}")
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        
        return None

    async def set_reverse_geocode(
        self,
        lat: float,
        lng: float,
        results: dict[str, Any],
    ) -> bool:
        """
        Cache reverse geocoding results.
        
        Args:
            lat: Latitude
            lng: Longitude
            results: Reverse geocoding results to cache
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        lat_rounded = round(lat, 4)
        lng_rounded = round(lng, 4)
        key = self._make_key("reverse_geocode", lat_rounded, lng_rounded)
        
        try:
            await cache.client.setex(
                key,
                self.TTL_REVERSE_GEOCODE,
                json.dumps(results)
            )
            logger.debug(f"Cache SET: reverse_geocode {lat},{lng}")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def get_categories(self) -> list[dict[str, Any]] | None:
        """
        Get cached categories.
        
        Returns:
            Cached categories or None
        """
        if not self.enabled:
            return None

        key = "categories"
        
        try:
            cached = await cache.client.get(key)
            if cached:
                logger.debug("Cache HIT: categories")
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        
        return None

    async def set_categories(self, categories: list[dict[str, Any]]) -> bool:
        """
        Cache categories.
        
        Args:
            categories: Categories list to cache
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        key = "categories"
        
        try:
            await cache.client.setex(
                key,
                self.TTL_CATEGORIES,
                json.dumps(categories)
            )
            logger.debug("Cache SET: categories")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def get_brands(
        self,
        category: str | None = None
    ) -> list[dict[str, Any]] | None:
        """
        Get cached brands.
        
        Args:
            category: Optional category filter
            
        Returns:
            Cached brands or None
        """
        if not self.enabled:
            return None

        key = f"brands:{category}" if category else "brands"
        
        try:
            cached = await cache.client.get(key)
            if cached:
                logger.debug(f"Cache HIT: brands ({category})")
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        
        return None

    async def set_brands(
        self,
        brands: list[dict[str, Any]],
        category: str | None = None
    ) -> bool:
        """
        Cache brands.
        
        Args:
            brands: Brands list to cache
            category: Optional category filter
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        key = f"brands:{category}" if category else "brands"
        
        try:
            await cache.client.setex(
                key,
                self.TTL_BRANDS,
                json.dumps(brands)
            )
            logger.debug(f"Cache SET: brands ({category})")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def get_autocomplete(
        self,
        query: str,
        lat: float | None,
        lng: float | None,
    ) -> list[dict[str, Any]] | None:
        """
        Get cached autocomplete results.
        
        Args:
            query: Search query
            lat: Optional latitude
            lng: Optional longitude
            
        Returns:
            Cached suggestions or None
        """
        if not self.enabled:
            return None

        key = self._make_key("autocomplete", query, lat, lng)
        
        try:
            cached = await cache.client.get(key)
            if cached:
                logger.debug(f"Cache HIT: autocomplete {query}")
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        
        return None

    async def set_autocomplete(
        self,
        query: str,
        lat: float | None,
        lng: float | None,
        suggestions: list[dict[str, Any]],
    ) -> bool:
        """
        Cache autocomplete results.
        
        Args:
            query: Search query
            lat: Optional latitude
            lng: Optional longitude
            suggestions: Suggestions to cache
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        key = self._make_key("autocomplete", query, lat, lng)
        
        try:
            await cache.client.setex(
                key,
                self.TTL_AUTOCOMPLETE,
                json.dumps(suggestions)
            )
            logger.debug(f"Cache SET: autocomplete {query}")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate cache keys matching a pattern.
        
        Args:
            pattern: Redis key pattern (e.g., "nearby:*")
            
        Returns:
            Number of keys invalidated
        """
        if not self.enabled:
            return 0

        try:
            keys = []
            async for key in cache.client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                await cache.client.delete(*keys)
                logger.info(f"Cache INVALIDATED: {len(keys)} keys matching '{pattern}'")
                return len(keys)
        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")
        
        return 0

    async def flush_all(self) -> bool:
        """
        Flush all cache keys.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            await cache.client.flushdb()
            logger.warning("Cache FLUSHED: all keys")
            return True
        except Exception as e:
            logger.error(f"Cache flush error: {e}")
            return False

    async def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Cache statistics
        """
        if not self.enabled:
            return {"enabled": False}

        try:
            info = await cache.client.info()
            keyspace = info.get("used_memory_human", "0B")
            return {
                "enabled": True,
                "keyspace": keyspace,
                "connected": True,
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {
                "enabled": True,
                "connected": False,
                "error": str(e),
            }


# Global cache service instance
geo_cache = GeoCacheService()


def get_geo_cache() -> GeoCacheService:
    """Get the global geo cache service instance."""
    return geo_cache
