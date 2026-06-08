"""
Redis Cache Service for Geo Search

Caches geo search results, geocoding results, and frequently accessed data
to improve performance and reduce database load.

Includes SQLite backup cache for offline persistence.
"""

import json
import logging
from typing import Any

from src.cache import cache
from src.services.geo_sqlite_cache import sqlite_cache

logger = logging.getLogger(__name__)


class GeoCacheService:
    """
    Redis caching service for geo search operations with SQLite backup.

    Cache TTL:
    - Nearby search: 15 minutes
    - Full-text search: 10 minutes
    - Geocoding: 1 hour
    - Reverse geocoding: 1 hour
    - Categories: 1 hour
    - Brands: 1 hour
    - Autocomplete: 5 minutes

    Fallback: SQLite cache when Redis is unavailable.
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
            logger.warning("⚠️  Redis cache service disabled, using SQLite backup")

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
        if self.enabled:
            key = self._make_key("nearby", lat, lng, radius_km, category, brand)

            try:
                cached = await cache.client.get(key)
                if cached:
                    logger.debug(f"Redis cache HIT: nearby {lat},{lng},{radius_km}")
                    return json.loads(cached)
            except Exception as e:
                logger.error(f"Redis cache get error: {e}")

        # Fallback to SQLite
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
        if self.enabled:
            key = self._make_key("nearby", lat, lng, radius_km, category, brand)

            try:
                await cache.client.setex(key, self.TTL_NEARBY, json.dumps(results))
                logger.debug(f"Redis cache SET: nearby {lat},{lng},{radius_km}")
                return True
            except Exception as e:
                logger.error(f"Redis cache set error: {e}")

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
        if self.enabled:
            key = self._make_key("search", query, lat, lng, radius_km, category, brand)

            try:
                cached = await cache.client.get(key)
                if cached:
                    logger.debug(f"Redis cache HIT: search {query}")
                    return json.loads(cached)
            except Exception as e:
                logger.error(f"Redis cache get error: {e}")

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
        if self.enabled:
            key = self._make_key("search", query, lat, lng, radius_km, category, brand)

            try:
                await cache.client.setex(key, self.TTL_SEARCH, json.dumps(results))
                logger.debug(f"Redis cache SET: search {query}")
                return True
            except Exception as e:
                logger.error(f"Redis cache set error: {e}")

        return False

    async def get_geocode(self, address: str) -> dict[str, Any] | None:
        """
        Get cached geocoding results.

        Args:
            address: Address to geocode

        Returns:
            Cached results or None
        """
        # Try Redis first
        if self.enabled:
            key = self._make_key("geocode", address.lower().strip())

            try:
                cached = await cache.client.get(key)
                if cached:
                    logger.debug(f"Redis cache HIT: geocode {address}")
                    return json.loads(cached)
            except Exception as e:
                logger.error(f"Redis cache get error: {e}")

        # Fallback to SQLite
        cached = sqlite_cache.lookup(address)
        if cached:
            logger.debug(f"SQLite cache HIT: geocode {address}")
            return {
                "latitude": cached["latitude"],
                "longitude": cached["longitude"],
                "source": "sqlite",
                "metadata": {
                    "country": cached["country"],
                    "city": cached["city"],
                    "district": cached["district"],
                    "ward": cached["ward"],
                    "street": cached["street"],
                    "postal_code": cached["postal_code"],
                },
            }

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
        success = False

        # Try Redis first
        if self.enabled:
            key = self._make_key("geocode", address.lower().strip())

            try:
                await cache.client.setex(key, self.TTL_GEOCODE, json.dumps(results))
                logger.debug(f"Redis cache SET: geocode {address}")
                success = True
            except Exception as e:
                logger.error(f"Redis cache set error: {e}")

        # Always save to SQLite as backup
        sqlite_cache.save(
            address=address,
            latitude=results.get("latitude"),
            longitude=results.get("longitude"),
            full_response=results,
            source_api="unknown",
            metadata=results.get("metadata", {}),
        )

        return success

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
        if self.enabled:
            # Round coordinates to reduce cache fragmentation
            lat_rounded = round(lat, 4)
            lng_rounded = round(lng, 4)

            key = self._make_key("reverse_geocode", lat_rounded, lng_rounded)

            try:
                cached = await cache.client.get(key)
                if cached:
                    logger.debug(f"Redis cache HIT: reverse_geocode {lat},{lng}")
                    return json.loads(cached)
            except Exception as e:
                logger.error(f"Redis cache get error: {e}")

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
        if self.enabled:
            lat_rounded = round(lat, 4)
            lng_rounded = round(lng, 4)

            key = self._make_key("reverse_geocode", lat_rounded, lng_rounded)

            try:
                await cache.client.setex(
                    key, self.TTL_REVERSE_GEOCODE, json.dumps(results)
                )
                logger.debug(f"Redis cache SET: reverse_geocode {lat},{lng}")
                return True
            except Exception as e:
                logger.error(f"Redis cache set error: {e}")

        return False

    async def get_categories(self) -> dict[str, Any] | None:
        """
        Get cached categories.

        Returns:
            Cached categories or None
        """
        if self.enabled:
            key = self._make_key("categories")

            try:
                cached = await cache.client.get(key)
                if cached:
                    logger.debug("Redis cache HIT: categories")
                    return json.loads(cached)
            except Exception as e:
                logger.error(f"Redis cache get error: {e}")

        return None

    async def set_categories(self, results: dict[str, Any]) -> bool:
        """
        Cache categories.

        Args:
            results: Categories to cache

        Returns:
            True if successful, False otherwise
        """
        if self.enabled:
            key = self._make_key("categories")

            try:
                await cache.client.setex(key, self.TTL_CATEGORIES, json.dumps(results))
                logger.debug("Redis cache SET: categories")
                return True
            except Exception as e:
                logger.error(f"Redis cache set error: {e}")

        return False

    async def get_brands(self) -> dict[str, Any] | None:
        """
        Get cached brands.

        Returns:
            Cached brands or None
        """
        if self.enabled:
            key = self._make_key("brands")

            try:
                cached = await cache.client.get(key)
                if cached:
                    logger.debug("Redis cache HIT: brands")
                    return json.loads(cached)
            except Exception as e:
                logger.error(f"Redis cache get error: {e}")

        return None

    async def set_brands(self, results: dict[str, Any]) -> bool:
        """
        Cache brands.

        Args:
            results: Brands to cache

        Returns:
            True if successful, False otherwise
        """
        if self.enabled:
            key = self._make_key("brands")

            try:
                await cache.client.setex(key, self.TTL_BRANDS, json.dumps(results))
                logger.debug("Redis cache SET: brands")
                return True
            except Exception as e:
                logger.error(f"Redis cache set error: {e}")

        return False

    async def get_autocomplete(
        self,
        query: str,
        lat: float | None = None,
        lng: float | None = None,
    ) -> dict[str, Any] | None:
        """
        Get cached autocomplete results.

        Args:
            query: Search query
            lat: Optional latitude
            lng: Optional longitude

        Returns:
            Cached results or None
        """
        if self.enabled:
            key = self._make_key("autocomplete", query, lat, lng)

            try:
                cached = await cache.client.get(key)
                if cached:
                    logger.debug(f"Redis cache HIT: autocomplete {query}")
                    return json.loads(cached)
            except Exception as e:
                logger.error(f"Redis cache get error: {e}")

        return None

    async def set_autocomplete(
        self,
        query: str,
        results: dict[str, Any],
        lat: float | None = None,
        lng: float | None = None,
    ) -> bool:
        """
        Cache autocomplete results.

        Args:
            query: Search query
            results: Autocomplete results to cache
            lat: Optional latitude
            lng: Optional longitude

        Returns:
            True if successful, False otherwise
        """
        if self.enabled:
            key = self._make_key("autocomplete", query, lat, lng)

            try:
                await cache.client.setex(
                    key, self.TTL_AUTOCOMPLETE, json.dumps(results)
                )
                logger.debug(f"Redis cache SET: autocomplete {query}")
                return True
            except Exception as e:
                logger.error(f"Redis cache set error: {e}")

        return False

    def get_sqlite_stats(self) -> dict:
        """Get SQLite cache statistics"""
        return sqlite_cache.get_stats()

    def clear_sqlite_cache(self):
        """Clear SQLite cache"""
        sqlite_cache.clear_cache()


# Global instance
geo_cache = GeoCacheService()


def get_geo_cache() -> GeoCacheService:
    """Get the global geo cache service instance."""
    return geo_cache
