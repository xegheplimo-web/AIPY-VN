"""
Geo Search API - Self-hosted spatial search endpoints

Provides REST API endpoints for geo search using PostGIS.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.services.geo_cache import GeoCacheService, get_geo_cache
from src.services.geo_search import GeoSearchService
from src.services.geo_service import GeoService, get_geo_service as get_smart_geo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/geo", tags=["Geo Search"])


async def get_geo_service(session: AsyncSession = Depends(get_db)) -> GeoSearchService:
    """Dependency injection for GeoSearchService."""
    cache = get_geo_cache()
    return GeoSearchService(session, cache=cache)


async def get_smart_geo_service() -> GeoService:
    """Dependency injection for GeoService (external API + L1/L2 cache)."""
    return get_smart_geo()


@router.get("/search")
async def search_stores(
    q: str = Query(..., min_length=1, description="Từ khóa tìm kiếm"),
    lat: float | None = Query(None, description="Latitude"),
    lng: float | None = Query(None, description="Longitude"),
    radius: float = Query(50, description="Bán kính (km)"),
    category: str | None = Query(None, description="Slug danh mục"),
    brand: str | None = Query(None, description="Slug thương hiệu"),
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
    category: str | None = Query(None),
    brand: str | None = Query(None),
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
    category: str | None = Query(None),
    svc: GeoSearchService = Depends(get_geo_service),
):
    """📋 Danh sách thương hiệu."""
    return await svc.get_brands(category)


@router.get("/autocomplete")
async def autocomplete(
    q: str = Query(..., min_length=1),
    lat: float | None = Query(None),
    lng: float | None = Query(None),
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
async def cache_stats(
    cache: GeoCacheService = Depends(get_geo_cache),
    smart_geo: GeoService = Depends(get_smart_geo_service),
):
    """📊 Thống kê cache (Redis L1 + SQLite L2)."""
    redis_stats = await cache.get_stats()
    memory_stats = smart_geo.get_stats()
    return {
        "redis_l1": redis_stats,
        "sqlite_l2": memory_stats,
    }


@router.get("/geocode/external")
async def geocode_external(
    address: str = Query(..., description="Địa chỉ cần geocode"),
    api: str = Query("nominatim", description="API provider: nominatim|google|goong"),
    force_refresh: bool = Query(False, description="Bỏ qua cache"),
    svc: GeoService = Depends(get_smart_geo_service),
):
    """
    🌍 Địa chỉ → Tọa độ (external API + auto cache).

    Tự động kiểm tra Redis → SQLite → API.
    Kết quả API tự động lưu vào cả 2 tầng cache.
    """
    result = await svc.geocode(address, api=api, force_refresh=force_refresh)
    if not result:
        raise HTTPException(status_code=404, detail="Không tìm thấy địa chỉ")
    return result


@router.get("/reverse/external")
async def reverse_geocode_external(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    api: str = Query("nominatim", description="API provider"),
    svc: GeoService = Depends(get_smart_geo_service),
):
    """🌍 Tọa độ → Địa chỉ (external API + auto cache)."""
    result = await svc.reverse_geocode(lat, lng, api=api)
    if not result:
        raise HTTPException(status_code=404, detail="Không tìm thấy địa chỉ")
    return result


@router.post("/batch/geocode")
async def batch_geocode(
    addresses: list[str],
    api: str = Query("nominatim", description="API provider"),
    svc: GeoService = Depends(get_smart_geo_service),
):
    """
    🌍 Geocode nhiều địa chỉ cùng lúc.

    Chỉ gọi API cho địa chỉ chưa có trong cache.
    """
    return await svc.batch_geocode(addresses, api=api)


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
