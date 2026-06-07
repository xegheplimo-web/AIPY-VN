from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import math

router = APIRouter(prefix="/api", tags=["Search"])


class ChatSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Câu hỏi/từ khóa tìm kiếm")
    location: Optional[dict] = Field(None, description={"lat": float, "lng": float})
    radius_km: float = Field(default=5.0, ge=0.1, le=50.0)
    limit: int = Field(default=10, ge=1, le=50)


class ProductResult(BaseModel):
    id: str
    name: str
    price: Optional[float]
    stock: Optional[int]
    in_stock: bool
    shelf_location: str
    category: Optional[str]


class StoreResult(BaseModel):
    id: str
    name: str
    address: str
    latitude: float
    longitude: float
    distance_m: Optional[float]
    industry: Optional[str]
    products: List[ProductResult]
    map_url: str


class ChatSearchResponse(BaseModel):
    summary: str
    stores: List[StoreResult]
    total_found: int


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371e3
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@router.post("/chat/search", response_model=ChatSearchResponse)
async def chat_search(req: ChatSearchRequest):
    # Mock data for demonstration
    stores = [
        StoreResult(
            id="store_001",
            name="Nhà thuốc An Khang",
            address="123 Nguyễn Trãi, Phường Bến Thành, Quận 1",
            latitude=10.776912,
            longitude=106.700934,
            distance_m=350,
            industry="Bán lẻ dược phẩm",
            products=[
                ProductResult(
                    id="p_123",
                    name="Panadol Extra 500mg",
                    price=35000,
                    stock=12,
                    in_stock=True,
                    shelf_location="Kệ A1, Tầng 1",
                    category="Thuốc giảm đau"
                )
            ],
            map_url="https://www.google.com/maps/dir/?api=1&destination=10.776912,106.700934&q=Nhà+thuốc+An+Khang"
        ),
        StoreResult(
            id="store_002",
            name="Nhà thuốc ABC",
            address="456 Lê Lợi, Quận 1",
            latitude=10.775123,
            longitude=106.701234,
            distance_m=680,
            industry="Bán lẻ dược phẩm",
            products=[
                ProductResult(
                    id="p_124",
                    name="Panadol Extra 500mg",
                    price=33000,
                    stock=5,
                    in_stock=True,
                    shelf_location="Kệ B2, Tầng 1",
                    category="Thuốc giảm đau"
                )
            ],
            map_url="https://www.google.com/maps/dir/?api=1&destination=10.775123,106.701234&q=Nhà+thuốc+ABC"
        )
    ]

    summary = f"✅ Tìm thấy {len(stores)} cửa hàng có '{req.query}' gần bạn"
    if stores and stores[0].distance_m and stores[0].distance_m < 500:
        summary += f" • Gần nhất chỉ {stores[0].distance_m}m 🎯"
    summary += ". Nhấn vào cửa hàng để xem chi tiết!"

    return ChatSearchResponse(
        summary=summary,
        stores=stores,
        total_found=len(stores)
    )


@router.get("/suggestions")
async def get_suggestions(q: str, limit: int = 5):
    suggestions = [
        "Panadol giảm đau",
        "Panadol Extra 500mg",
        "Vitamin C",
        "Khẩu trang y tế",
        "Nước rửa tay"
    ]
    return {"suggestions": [s for s in suggestions if q.lower() in s.lower()][:limit]}
