"""
Store Locator API

Endpoints for finding stores using OpenStreetMap (free, no API key required).
"""

import logging
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from src.services.store_locator import get_store_locator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/store-locator", tags=["Store Locator"])
locator = get_store_locator()


@router.get("/search")
async def search_stores(
    q: str = Query(..., description="Tên cửa hàng hoặc chuỗi"),
    city: str = Query(default="Hồ Chí Minh", description="Thành phố"),
    limit: int = Query(default=20, le=100, description="Số lượng kết quả"),
):
    """
    Tìm kiếm cửa hàng theo tên.

    Ví dụ:
        - Circle K
        - Bách Hóa Xanh
        - Highland Coffee
        - Thế Giới Di Động
        - Pharmacity
    """
    stores = await locator.search_stores_by_name(query=q, city=city, limit=limit)
    return {
        "total": len(stores),
        "query": q,
        "city": city,
        "stores": [
            {
                "name": s.name,
                "lat": s.latitude,
                "lng": s.longitude,
                "address": s.address,
                "city": s.city,
                "district": s.district,
                "ward": s.ward,
                "phone": s.phone,
                "category": s.category,
                "opening_hours": s.opening_hours,
            }
            for s in stores[:limit]
        ],
    }


@router.get("/nearby")
async def find_nearby(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    category: str = Query(default="convenience", description="Loại cửa hàng"),
    radius: float = Query(default=2, description="Bán kính (km)"),
    limit: int = Query(default=10, le=50, description="Số lượng kết quả"),
):
    """
    Tìm cửa hàng gần nhất từ vị trí hiện tại.

    Categories:
        - supermarket: Siêu thị
        - convenience: Cửa hàng tiện lợi
        - cafe: Quán cà phê
        - restaurant: Nhà hàng
        - pharmacy: Nhà thuốc
        - bank: Ngân hàng
        - fuel: Cây xăng
        - bakery: Tiệm bánh
        - fast_food: Fast food
    """
    results = locator.find_nearest_stores(
        lat=lat,
        lon=lng,
        category=category,
        radius_km=radius,
        limit=limit,
    )
    return {
        "total": len(results),
        "location": {"lat": lat, "lng": lng},
        "category": category,
        "radius_km": radius,
        "stores": results,
    }


@router.get("/geocode")
async def geocode(
    address: str = Query(..., description="Địa chỉ cần tìm tọa độ"),
):
    """
    Chuyển địa chỉ → tọa độ.

    Priority: OpenMap.vn → Nominatim

    Ví dụ: "123 Nguyễn Huệ, Quận 1, TP.HCM"
    """
    result = await locator.geocode_address(address)
    if not result:
        raise HTTPException(status_code=404, detail="Không tìm thấy địa chỉ")
    return result


@router.get("/reverse-geocode")
async def reverse_geocode(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
):
    """
    Chuyển tọa độ → địa chỉ đầy đủ.

    Priority: OpenMap.vn → Nominatim

    Ví dụ: (10.7769, 106.7009) → "123 Nguyễn Huệ, Phường Bến Nghé, Quận 1, TP.HCM"
    """
    return await locator.reverse_geocode(lat, lng)


@router.get("/category/{category}")
async def stores_by_category(
    category: str,
    city: str = Query(default="Hồ Chí Minh", description="Thành phố"),
    radius: float = Query(default=10, description="Bán kính (km)"),
):
    """
    Lấy tất cả cửa hàng theo loại trong khu vực.

    Categories:
        - supermarket: Siêu thị
        - convenience: Cửa hàng tiện lợi
        - cafe: Quán cà phê
        - restaurant: Nhà hàng
        - pharmacy: Nhà thuốc
        - bank: Ngân hàng
        - atm: ATM
        - hospital: Bệnh viện
        - school: Trường học
        - fuel: Cây xăng
        - bakery: Tiệm bánh
        - fast_food: Fast food
        - clothes: Cửa hàng quần áo
        - electronics: Cửa hàng điện tử
        - mobile_phone: Cửa hàng điện thoại
    """
    stores = locator.search_stores_by_area(
        category=category,
        city=city,
        radius_km=radius,
    )
    return {
        "category": category,
        "city": city,
        "radius_km": radius,
        "total": len(stores),
        "stores": [
            {
                "name": s.name,
                "lat": s.latitude,
                "lng": s.longitude,
                "address": s.address,
                "district": s.district,
                "ward": s.ward,
                "phone": s.phone,
                "hours": s.opening_hours,
                "website": s.website,
            }
            for s in stores
        ],
    }


@router.get("/chains")
async def list_popular_chains():
    """
    Lấy danh sách chuỗi cửa hàng phổ biến tại Việt Nam.
    """
    chains = [
        "Bách Hóa Xanh",
        "Thế Giới Di Động",
        "FPT Shop",
        "Pharmacity",
        "Highland Coffee",
        "GS25",
        "Ministop",
        "7-Eleven",
        "Circle K",
        "VinMart",
        "Co.op Mart",
        "Coffee House",
        "The Coffee House",
        "Phuc Long",
    ]
    return {
        "total": len(chains),
        "chains": chains,
    }
