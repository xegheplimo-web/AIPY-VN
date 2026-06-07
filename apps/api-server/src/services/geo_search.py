"""
Geo Search Service - Self-hosted spatial search using PostGIS

This service provides fast, offline-capable geo search for Vietnam
without depending on external APIs like Google Maps or OpenStreetMap.
"""

import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.services.geo_cache import GeoCacheService, get_geo_cache

logger = logging.getLogger(__name__)


class GeoSearchService:
    """
    Self-hosted geo search service using PostGIS.

    Features:
    - Full-text search with Vietnamese text normalization
    - Fuzzy matching (trigram index)
    - Spatial queries (nearby search)
    - Geocoding and reverse geocoding
    - Category and brand filtering
    - Redis caching for performance
    """

    def __init__(self, session: AsyncSession, cache: Optional[GeoCacheService] = None):
        self.session = session
        self.cache = cache or get_geo_cache()

    async def search(
        self,
        query: str,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        radius_km: float = 50,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Intelligent search with full-text, fuzzy, and spatial filtering.

        Args:
            query: Search query (Vietnamese text supported)
            lat: Optional latitude for geo filtering
            lng: Optional longitude for geo filtering
            radius_km: Search radius in km
            category: Optional category slug filter
            brand: Optional brand slug filter
            limit: Number of results
            offset: Pagination offset

        Returns:
            Search results with metadata
        """
        # Check cache first
        cached = await self.cache.get_search(
            query, lat, lng, radius_km, category, brand
        )
        if cached:
            logger.debug(f"Cache HIT: search {query}")
            return cached

        try:
            # Get category_id
            cat_id = None
            if category:
                result = await self.session.execute(
                    text("SELECT id FROM store_categories WHERE slug = :slug"),
                    {"slug": category},
                )
                row = result.fetchone()
                cat_id = row[0] if row else None

            # Get brand_id
            brand_id = None
            if brand:
                result = await self.session.execute(
                    text("SELECT id FROM brands WHERE slug = :slug"), {"slug": brand}
                )
                row = result.fetchone()
                brand_id = row[0] if row else None

            # Main search query
            rows = await self.session.execute(
                text(
                    """
                SELECT 
                    s.id,
                    s.name,
                    s.latitude,
                    s.longitude,
                    CASE 
                        WHEN :lat IS NOT NULL AND :lng IS NOT NULL
                        THEN ST_Distance(
                            s.location::geography,
                            ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
                        )
                        ELSE NULL
                    END AS distance_meters,
                    s.full_address,
                    s.phone,
                    b.name AS brand_name,
                    b.logo_url AS brand_logo,
                    c.name_vi AS category_name,
                    c.icon AS category_icon,
                    s.rating,
                    s.review_count,
                    s.opening_hours,
                    s.images,
                    GREATEST(
                        ts_rank(s.search_text, plainto_tsquery('simple', :query)),
                        ts_rank(
                            s.search_text, 
                            plainto_tsquery('simple', vn_unaccent(:query))
                        ),
                        similarity(
                            s.name_normalized, 
                            lower(vn_unaccent(:query))
                        )
                    ) AS relevance
                FROM stores s
                LEFT JOIN brands b ON s.brand_id = b.id
                LEFT JOIN store_categories c ON s.category_id = c.id
                WHERE s.is_active = TRUE
                    AND (
                        s.search_text @@ plainto_tsquery('simple', :query)
                        OR s.search_text @@ plainto_tsquery(
                            'simple', vn_unaccent(:query)
                        )
                        OR s.name_normalized %% lower(vn_unaccent(:query))
                        OR s.name_normalized ILIKE '%' || vn_unaccent(:query) || '%'
                    )
                    AND (:cat_id IS NULL OR s.category_id = :cat_id)
                    AND (:brand_id IS NULL OR s.brand_id = :brand_id)
                    AND (
                        :lat IS NULL OR :lng IS NULL
                        OR ST_DWithin(
                            s.location::geography,
                            ST_SetSRID(
                                ST_MakePoint(:lng, :lat), 4326
                            )::geography,
                            :radius_km * 1000
                        )
                    )
                ORDER BY 
                    relevance DESC,
                    CASE 
                        WHEN :lat IS NOT NULL AND :lng IS NOT NULL
                        THEN ST_Distance(
                            s.location::geography,
                            ST_SetSRID(
                                ST_MakePoint(:lng, :lat), 4326
                            )::geography
                        )
                        ELSE 0
                    END ASC,
                    s.rating DESC
                LIMIT :limit OFFSET :offset
            """
                ),
                {
                    "query": query,
                    "lat": lat,
                    "lng": lng,
                    "cat_id": cat_id,
                    "brand_id": brand_id,
                    "radius_km": radius_km,
                    "limit": limit,
                    "offset": offset,
                },
            )

            # Total count
            total_result = await self.session.execute(
                text(
                    """
                SELECT COUNT(*) FROM stores s
                WHERE s.is_active = TRUE
                    AND (
                        s.search_text @@ plainto_tsquery('simple', :query)
                        OR s.search_text @@ plainto_tsquery(
                            'simple', vn_unaccent(:query)
                        )
                        OR s.name_normalized %% lower(vn_unaccent(:query))
                        OR s.name_normalized ILIKE '%' || vn_unaccent(:query) || '%'
                    )
                    AND (:cat_id IS NULL OR s.category_id = :cat_id)
            """
                ),
                {"query": query, "cat_id": cat_id},
            )

            total = total_result.scalar() or 0

            stores = []
            for row in rows:
                dist = row.distance_meters
                stores.append(
                    {
                        "id": row.id,
                        "name": row.name,
                        "lat": row.latitude,
                        "lng": row.longitude,
                        "distance": (
                            {
                                "meters": round(dist) if dist else None,
                                "text": self._format_distance(dist) if dist else None,
                            }
                            if dist
                            else None
                        ),
                        "address": row.full_address,
                        "phone": row.phone,
                        "brand": (
                            {
                                "name": row.brand_name,
                                "logo": row.brand_logo,
                            }
                            if row.brand_name
                            else None
                        ),
                        "category": {
                            "name": row.category_name,
                            "icon": row.category_icon,
                        },
                        "rating": float(row.rating) if row.rating else 0,
                        "review_count": row.review_count,
                        "opening_hours": row.opening_hours,
                        "images": row.images or [],
                        "relevance": round(float(row.relevance), 3),
                    }
                )

            result = {
                "query": query,
                "total": total,
                "limit": limit,
                "offset": offset,
                "stores": stores,
            }

            # Cache the result
            await self.cache.set_search(
                query, lat, lng, radius_km, category, brand, result
            )

            return result

        except Exception as e:
            logger.error(f"Search error: {e}")
            return {
                "query": query,
                "total": 0,
                "limit": limit,
                "offset": offset,
                "stores": [],
                "error": str(e),
            }

    async def find_nearby(
        self,
        lat: float,
        lng: float,
        radius_km: float = 5,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Find stores near a location using PostGIS spatial query.

        Args:
            lat: Latitude
            lng: Longitude
            radius_km: Search radius in km
            category: Optional category slug
            brand: Optional brand slug
            limit: Number of results

        Returns:
            Nearby stores with distance information
        """
        # Check cache first
        cached = await self.cache.get_nearby(lat, lng, radius_km, category, brand)
        if cached:
            logger.debug(f"Cache HIT: nearby {lat},{lng},{radius_km}")
            return cached

        try:
            cat_id = None
            if category:
                result = await self.session.execute(
                    text("SELECT id FROM store_categories WHERE slug = :slug"),
                    {"slug": category},
                )
                row = result.fetchone()
                cat_id = row[0] if row else None

            brand_id = None
            if brand:
                result = await self.session.execute(
                    text("SELECT id FROM brands WHERE slug = :slug"), {"slug": brand}
                )
                row = result.fetchone()
                brand_id = row[0] if row else None

            rows = await self.session.execute(
                text(
                    """
                SELECT * FROM find_nearest_stores(
                    :lat, :lng, :radius_km, :cat_id, :brand_id, :limit
                )
            """
                ),
                {
                    "lat": lat,
                    "lng": lng,
                    "radius_km": radius_km,
                    "cat_id": cat_id,
                    "brand_id": brand_id,
                    "limit": limit,
                },
            )

            result = {
                "center": {"lat": lat, "lng": lng},
                "radius_km": radius_km,
                "total": len(rows.fetchall()),
                "stores": [
                    {
                        "id": r.store_id,
                        "name": r.store_name,
                        "lat": r.lat,
                        "lng": r.lng,
                        "distance": {
                            "meters": round(r.distance_meters),
                            "text": r.distance_text,
                        },
                        "address": r.full_address,
                        "phone": r.phone,
                        "brand": r.brand_name,
                        "category": {
                            "name": r.category_name,
                            "icon": r.category_icon,
                        },
                        "rating": float(r.rating) if r.rating else 0,
                        "hours": r.opening_hours,
                    }
                    for r in rows
                ],
            }

            # Cache the result
            await self.cache.set_nearby(lat, lng, radius_km, category, brand, result)

            return result

        except Exception as e:
            logger.error(f"Nearby search error: {e}")
            return {
                "center": {"lat": lat, "lng": lng},
                "radius_km": radius_km,
                "total": 0,
                "stores": [],
                "error": str(e),
            }

    async def geocode(self, address: str) -> Dict[str, Any]:
        """
        Geocode address to coordinates using Vietnam admin data.

        Args:
            address: Address string

        Returns:
            Geocoding results with coordinates
        """
        # Check cache first
        cached = await self.cache.get_geocode(address)
        if cached:
            logger.debug(f"Cache HIT: geocode {address}")
            return cached

        try:
            rows = await self.session.execute(
                text("SELECT * FROM geocode_address(:query)"), {"query": address}
            )

            result = {
                "query": address,
                "results": [
                    {
                        "lat": r.lat,
                        "lng": r.lng,
                        "display_name": r.display_name,
                        "ward": r.ward_name,
                        "district": r.district_name,
                        "province": r.province_name,
                        "confidence": round(float(r.confidence), 3),
                    }
                    for r in rows
                ],
            }

            # Cache the result
            await self.cache.set_geocode(address, result)

            return result

        except Exception as e:
            logger.error(f"Geocode error: {e}")
            return {
                "query": address,
                "results": [],
                "error": str(e),
            }

    async def reverse_geocode(self, lat: float, lng: float) -> Dict[str, Any]:
        """
        Reverse geocode coordinates to address.

        Args:
            lat: Latitude
            lng: Longitude

        Returns:
            Address information
        """
        # Check cache first
        cached = await self.cache.get_reverse_geocode(lat, lng)
        if cached:
            logger.debug(f"Cache HIT: reverse_geocode {lat},{lng}")
            return cached

        try:
            row = await self.session.execute(
                text(
                    """
                SELECT 
                    w.name AS ward,
                    w.full_name AS ward_full,
                    d.name AS district,
                    d.full_name AS district_full,
                    p.name AS province,
                    p.full_name AS province_full,
                    ST_Distance(
                        w.center::geography,
                        ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
                    ) AS distance
                FROM wards w
                JOIN districts d ON w.district_code = d.code
                JOIN provinces p ON d.province_code = p.code
                WHERE w.center IS NOT NULL
                ORDER BY w.center <-> ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)
                LIMIT 1
            """
                ),
                {"lat": lat, "lng": lng},
            )

            result = row.fetchone()
            if not result:
                return {"lat": lat, "lng": lng, "address": None}

            # Find nearest street from stores
            street_row = await self.session.execute(
                text(
                    """
                SELECT street, house_number, full_address
                FROM stores
                WHERE street IS NOT NULL
                ORDER BY location <-> ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)
                LIMIT 1
            """
                ),
                {"lat": lat, "lng": lng},
            )

            street_result = street_row.fetchone()

            result_data = {
                "lat": lat,
                "lng": lng,
                "address": {
                    "street": street_result.street if street_result else None,
                    "house_number": (
                        street_result.house_number if street_result else None
                    ),
                    "ward": result.ward,
                    "district": result.district,
                    "province": result.province,
                    "full": (
                        f"{result.ward_full}, "
                        f"{result.district_full}, "
                        f"{result.province_full}"
                    ),
                },
            }

            # Cache the result
            await self.cache.set_reverse_geocode(lat, lng, result_data)

            return result_data

        except Exception as e:
            logger.error(f"Reverse geocode error: {e}")
            return {
                "lat": lat,
                "lng": lng,
                "address": None,
                "error": str(e),
            }

    async def get_categories(self) -> List[Dict[str, Any]]:
        """Get all store categories with store counts."""
        # Check cache first
        cached = await self.cache.get_categories()
        if cached:
            logger.debug("Cache HIT: categories")
            return cached

        try:
            rows = await self.session.execute(
                text(
                    """
                SELECT c.*, COUNT(s.id) AS store_count
                FROM store_categories c
                LEFT JOIN stores s ON c.id = s.category_id AND s.is_active
                WHERE c.is_active = TRUE
                GROUP BY c.id
                ORDER BY c.sort_order, store_count DESC
            """
                )
            )
            result = [dict(row) for row in rows]

            # Cache the result
            await self.cache.set_categories(result)

            return result
        except Exception as e:
            logger.error(f"Get categories error: {e}")
            return []

    async def get_brands(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all brands with store counts."""
        # Check cache first
        cached = await self.cache.get_brands(category)
        if cached:
            logger.debug(f"Cache HIT: brands ({category})")
            return cached

        try:
            query = """
                SELECT b.*, COUNT(s.id) AS store_count
                FROM brands b
                LEFT JOIN stores s ON b.id = s.brand_id AND s.is_active
                WHERE b.is_active = TRUE
            """
            params = {}

            if category:
                query += """
                    AND b.category_id = (
                        SELECT id FROM store_categories WHERE slug = :slug
                    )
                """
                params["slug"] = category

            query += " GROUP BY b.id ORDER BY store_count DESC"

            rows = await self.session.execute(text(query), params)
            result = [dict(row) for row in rows]

            # Cache the result
            await self.cache.set_brands(result, category)

            return result
        except Exception as e:
            logger.error(f"Get brands error: {e}")
            return []

    @staticmethod
    def _format_distance(meters: Optional[float]) -> Optional[str]:
        """Format distance in meters to human-readable string."""
        if meters is None:
            return None
        if meters < 1000:
            return f"{int(meters)}m"
        return f"{meters/1000:.1f}km"
