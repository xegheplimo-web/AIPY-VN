"""
Geo Search API - Self-hosted spatial search endpoints

Provides REST API endpoints for geo search using PostGIS.
"""

import logging
from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_db
from src.services.geo_search import GeoSearchService
from src.services.geo_cache import GeoCacheService, get_geo_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/geo", tags=["Geo Search"])


async def get_geo_service(session: AsyncSession = Depends(get_db)) -> GeoSearchService:
    """Dependency injection for GeoSearchService."""
    cache = get_geo_cache()
    return GeoSearchService(session, cache=cache)


@router.get("/search")
async def search_stores(
    q: str = Query(..., min_length=1, description="Từ khóa tìm kiếm"),
    lat: Optional[float] = Query(None, description="Latitude"),
    lng: Optional[float] = Query(None, description="Longitude"),
    radius: float = Query(50, description="Bán kính (km)"),
    category: Optional[str] = Query(None, description="Slug danh mục"),
    brand: Optional[str] = Query(None, description="Slug thương hiệu"),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    svc: GeoSearchService = Depends(get_geo_service),
):
    """
    🔍 Tìm kiếm cửa hàng thông minh.

    Hỗ trợ:
    - Tìm theo tên: `?q=Circle K`
    - Tìm gần vị trí: `?q=cafe&lat=10.77&lng=106.70`
    - Tìm theo danh mục: `?q=cà phê&category=cafe`
    - Tìm theo thương hiệu: `?q=&brand=highlands-coffee`
    - Gõ sai vẫn tìm được: `?q=hailend cofe`
    - Không dấu: `?q=ca phe`
    """
    return await svc.search(
        query=q,
        lat=lat,
        lng=lng,
        radius_km=radius,
        category=category,
        brand=brand,
        limit=limit,
        offset=offset,
    )


@router.get("/nearby")
async def find_nearby(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius: float = Query(5, description="Bán kính (km)"),
    category: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    svc: GeoSearchService = Depends(get_geo_service),
):
    """
    📍 Tìm cửa hàng gần nhất.

    Ví dụ: Tìm ATM gần Quận 1:
    `?lat=10.7769&lng=106.7009&category=atm&radius=2`
    """
    return await svc.find_nearby(
        lat=lat,
        lng=lng,
        radius_km=radius,
        category=category,
        brand=brand,
        limit=limit,
    )


@router.get("/geocode")
async def geocode(
    address: str = Query(..., description="Địa chỉ cần tìm tọa độ"),
    svc: GeoSearchService = Depends(get_geo_service),
):
    """
    📍 Địa chỉ → Tọa độ (self-hosted).

    Ví dụ: `?address=Nguyễn Huệ, Quận 1`
    """
    result = await svc.geocode(address)
    if not result["results"]:
        raise HTTPException(status_code=404, detail="Không tìm thấy địa chỉ")
    return result


@router.get("/reverse")
async def reverse_geocode(
    lat: float = Query(...),
    lng: float = Query(...),
    svc: GeoSearchService = Depends(get_geo_service),
):
    """
    📍 Tọa độ → Địa chỉ (self-hosted).
    """
    return await svc.reverse_geocode(lat, lng)


@router.get("/categories")
async def list_categories(
    svc: GeoSearchService = Depends(get_geo_service),
):
    """📋 Danh sách danh mục cửa hàng."""
    return await svc.get_categories()


@router.get("/brands")
async def list_brands(
    category: Optional[str] = Query(None),
    svc: GeoSearchService = Depends(get_geo_service),
):
    """📋 Danh sách thương hiệu."""
    return await svc.get_brands(category)


@router.get("/autocomplete")
async def autocomplete(
    q: str = Query(..., min_length=1),
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    limit: int = Query(8, le=20),
    svc: GeoSearchService = Depends(get_geo_service),
):
    """
    ⌨️ Gợi ý khi gõ (autocomplete).
    Trả về nhanh, tối ưu cho UX.
    """
    result = await svc.search(
        query=q,
        lat=lat,
        lng=lng,
        limit=limit,
    )

    return {
        "suggestions": [
            {
                "id": s["id"],
                "name": s["name"],
                "address": s["address"],
                "category_icon": (s["category"]["icon"] if s.get("category") else None),
                "distance": (s["distance"]["text"] if s.get("distance") else None),
            }
            for s in result["stores"]
        ]
    }


@router.get("/cache/stats")
async def cache_stats(cache: GeoCacheService = Depends(get_geo_cache)):
    """📊 Thống kê cache."""
    return await cache.get_stats()


@router.post("/cache/invalidate")
async def invalidate_cache(
    pattern: str = Query(..., description="Pattern để invalidate (ví dụ: 'nearby:*')"),
    cache: GeoCacheService = Depends(get_geo_cache),
):
    """
    🗑️ Invalidate cache theo pattern.

    Ví dụ: `?pattern=nearby:*` sẽ xóa tất cả nearby cache.
    """
    count = await cache.invalidate_pattern(pattern)
    return {
        "pattern": pattern,
        "invalidated": count,
        "message": f"Đã xóa {count} cache keys matching '{pattern}'",
    }


@router.post("/cache/flush")
async def flush_cache(cache: GeoCacheService = Depends(get_geo_cache)):
    """
    🗑️ Xóa toàn bộ cache.

    Cẩn thận: Sẽ xóa tất cả cache keys!
    """
    success = await cache.flush_all()
    return {
        "success": success,
        "message": "Đã xóa toàn bộ cache" if success else "Không thể xóa cache",
    }
