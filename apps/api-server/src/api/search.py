from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import re

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.database import async_session
from src.models.store import Product
from src.services.geo import haversine_distance

router = APIRouter(prefix="/api", tags=["Search"])


def sanitize_search_term(term: str) -> str:
    """Remove potentially dangerous characters from search term"""
    # Remove special SQL characters and limit length
    sanitized = re.sub(r"[;'\"]", "", term)
    # Limit to 200 characters to prevent DoS
    return sanitized[:200]


class ChatSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Cau hoi/tu khoa tim kiem")
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


@router.post("/chat/search", response_model=ChatSearchResponse)
async def chat_search(req: ChatSearchRequest):
    async with async_session() as session:
        # 1. Find products matching query (case-insensitive)
        search_term = f"%{sanitize_search_term(req.query)}%"
        stmt = (
            select(Product)
            .where(Product.name.ilike(search_term))
            .where(Product.stock > 0)
            .where(Product.status == "active")
            .options(selectinload(Product.store))
        )
        result = await session.execute(stmt)
        products = result.scalars().all()

        # 2. Group products by store
        store_products = {}
        for p in products:
            store_id = str(p.store_id)
            if store_id not in store_products:
                store_products[store_id] = {"store": p.store, "products": []}
            store_products[store_id]["products"].append(p)

        # 3. Calculate distance and filter by radius
        stores_result = []
        user_lat = None
        user_lng = None

        if req.location:
            if not isinstance(req.location, dict):
                raise HTTPException(status_code=422, detail="Location must be a dict")
            user_lat = req.location.get("lat")
            user_lng = req.location.get("lng")

            if user_lat is None or user_lng is None:
                raise HTTPException(
                    status_code=422, detail="Location must include lat and lng"
                )

            if not (-90 <= user_lat <= 90) or not (-180 <= user_lng <= 180):
                raise HTTPException(status_code=422, detail="Invalid coordinates")

        for store_id, data in store_products.items():
            store = data["store"]
            distance_m = None

            if user_lat is not None and user_lng is not None:
                distance_m = haversine_distance(
                    user_lat, user_lng, store.latitude, store.longitude
                )
                # Filter by radius
                if distance_m > req.radius_km * 1000:
                    continue

            # Build product results
            product_results = []
            for p in data["products"]:
                product_results.append(
                    ProductResult(
                        id=str(p.id),
                        name=p.name,
                        price=float(p.price) if p.price else None,
                        stock=p.stock,
                        in_stock=p.stock > 0,
                        shelf_location=p.shelf_location or "",
                        category=None,  # Can be added later
                    )
                )

            # Build map URL
            encoded_name = store.name.replace(" ", "+")
            map_url = f"https://www.google.com/maps/dir/?api=1&destination={store.latitude},{store.longitude}&q={encoded_name}"

            stores_result.append(
                StoreResult(
                    id=str(store.id),
                    name=store.name,
                    address=store.address,
                    latitude=store.latitude,
                    longitude=store.longitude,
                    distance_m=round(distance_m, 1) if distance_m is not None else None,
                    industry=store.industry,
                    products=product_results,
                    map_url=map_url,
                )
            )

        # 4. Sort by distance (nearest first)
        stores_result.sort(key=lambda x: x.distance_m if x.distance_m else float("inf"))

        # 5. Apply limit
        stores_result = stores_result[: req.limit]

        # 6. Build summary
        total = len(stores_result)
        if total == 0:
            summary = f"Khong tim thay '{req.query}' trong ban kinh {req.radius_km}km. Ban thu tim tu khoa khac nhe!"
        else:
            summary = f"Tim thay {total} cua hang co '{req.query}' gan ban"
            if stores_result[0].distance_m and stores_result[0].distance_m < 500:
                summary += f" • Gan nhat chi {stores_result[0].distance_m}m"
            summary += ". Nhan vao cua hang de xem chi tiet!"

        return ChatSearchResponse(
            summary=summary, stores=stores_result, total_found=total
        )


@router.get("/suggestions")
async def get_suggestions(q: str, limit: int = 5):
    async with async_session() as session:
        sanitized_q = sanitize_search_term(q)
        stmt = (
            select(Product.name)
            .where(Product.name.ilike(f"%{sanitized_q}%"))
            .where(Product.stock > 0)
            .limit(limit * 3)
        )
        result = await session.execute(stmt)
        names = [row[0] for row in result.all()]

        # Return unique names
        seen = set()
        unique = []
        for name in names:
            if name not in seen:
                seen.add(name)
                unique.append(name)
                if len(unique) >= limit:
                    break

        return {"suggestions": unique}
