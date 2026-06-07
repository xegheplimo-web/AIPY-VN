import uuid
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from src.db import async_session
from src.models.store import Store, Product, Category
from src.models.review import Review

router = APIRouter(prefix="/api/stores", tags=["Stores"])


class StoreListItem(BaseModel):
    id: str
    name: str
    address: str
    latitude: float
    longitude: float
    phone: Optional[str] = None
    email: Optional[str] = None
    logo_url: Optional[str] = None
    industry: Optional[str] = None
    is_open_now: Optional[bool] = None
    rating: Optional[float] = None
    total_reviews: Optional[int] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True


class StoreListResponse(BaseModel):
    stores: List[StoreListItem]
    total: int
    page: int
    limit: int


class StoreDetailResponse(BaseModel):
    id: str
    name: str
    address: str
    latitude: float
    longitude: float
    phone: Optional[str] = None
    email: Optional[str] = None
    zalo: Optional[str] = None
    logo_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    images: Optional[List[str]] = None
    business_hours: Optional[dict] = None
    is_open_now: Optional[bool] = None
    rating: Optional[float] = None
    total_reviews: Optional[int] = None
    industry: Optional[str] = None
    status: Optional[str] = None
    location_verified: Optional[bool] = None
    products_count: int
    average_rating: Optional[float] = None

    class Config:
        from_attributes = True


class StoreProductItem(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    unit: Optional[str] = None
    images: Optional[List[str]] = None
    shelf_location: Optional[str] = None
    category_name: Optional[str] = None

    class Config:
        from_attributes = True


class StoreProductsResponse(BaseModel):
    products: List[StoreProductItem]
    page: int
    limit: int
    total: int


class StoreRegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    address: str = Field(..., min_length=1)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    zalo: Optional[str] = Field(None, max_length=20)
    industry: Optional[str] = Field(None, max_length=100)


class StoreRegisterResponse(BaseModel):
    id: str
    status: str


class ValidateLocationRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


class ValidateLocationResponse(BaseModel):
    valid: bool
    message: str


@router.get("/", response_model=StoreListResponse)
async def list_stores(
    province: Optional[str] = None,
    industry: Optional[str] = None,
    is_open: Optional[bool] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    async with async_session() as session:
        stmt = select(Store).where(Store.status == "active")
        count_stmt = select(func.count(Store.id)).where(Store.status == "active")

        if province:
            stmt = stmt.where(Store.address.ilike(f"%{province}%"))
            count_stmt = count_stmt.where(Store.address.ilike(f"%{province}%"))

        if industry:
            stmt = stmt.where(Store.industry == industry)
            count_stmt = count_stmt.where(Store.industry == industry)

        if is_open is not None:
            stmt = stmt.where(Store.is_open_now == is_open)
            count_stmt = count_stmt.where(Store.is_open_now == is_open)

        # Pagination
        offset = (page - 1) * limit
        stmt = stmt.offset(offset).limit(limit)

        result = await session.execute(stmt)
        stores = result.scalars().all()

        total_result = await session.execute(count_stmt)
        total = total_result.scalar_one()

        store_items = [
            StoreListItem(
                id=str(s.id),
                name=s.name,
                address=s.address,
                latitude=s.latitude,
                longitude=s.longitude,
                phone=s.phone,
                email=s.email,
                logo_url=s.logo_url,
                industry=s.industry,
                is_open_now=s.is_open_now,
                rating=float(s.rating) if s.rating else None,
                total_reviews=s.total_reviews,
                status=s.status,
            )
            for s in stores
        ]

        return StoreListResponse(
            stores=store_items, total=total, page=page, limit=limit
        )


@router.get("/{store_id}", response_model=StoreDetailResponse)
async def get_store_detail(store_id: str):
    async with async_session() as session:
        # Get store
        stmt = select(Store).where(Store.id == uuid.UUID(store_id))
        result = await session.execute(stmt)
        store = result.scalar_one_or_none()

        if not store:
            raise HTTPException(status_code=404, detail="Store not found")

        # Count products
        products_count_stmt = select(func.count(Product.id)).where(
            Product.store_id == uuid.UUID(store_id),
            Product.status == "active",
        )
        products_count_result = await session.execute(products_count_stmt)
        products_count = products_count_result.scalar_one()

        # Average rating from reviews
        avg_rating_stmt = select(func.avg(Review.rating)).where(
            Review.store_id == uuid.UUID(store_id)
        )
        avg_rating_result = await session.execute(avg_rating_stmt)
        average_rating = avg_rating_result.scalar_one()

        return StoreDetailResponse(
            id=str(store.id),
            name=store.name,
            address=store.address,
            latitude=store.latitude,
            longitude=store.longitude,
            phone=store.phone,
            email=store.email,
            zalo=store.zalo,
            logo_url=store.logo_url,
            cover_image_url=store.cover_image_url,
            images=store.images,
            business_hours=store.business_hours,
            is_open_now=store.is_open_now,
            rating=float(store.rating) if store.rating else None,
            total_reviews=store.total_reviews,
            industry=store.industry,
            status=store.status,
            location_verified=store.location_verified,
            products_count=products_count,
            average_rating=float(average_rating) if average_rating else None,
        )


@router.get("/{store_id}/products", response_model=StoreProductsResponse)
async def get_store_products(
    store_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    async with async_session() as session:
        # Verify store exists
        store_stmt = select(Store).where(Store.id == uuid.UUID(store_id))
        store_result = await session.execute(store_stmt)
        store = store_result.scalar_one_or_none()
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")

        # Get paginated products with category
        offset = (page - 1) * limit
        stmt = (
            select(Product, Category.name.label("category_name"))
            .outerjoin(Category, Product.category_id == Category.id)
            .where(Product.store_id == uuid.UUID(store_id))
            .where(Product.status == "active")
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(stmt)
        rows = result.all()

        # Count total
        count_stmt = select(func.count(Product.id)).where(
            Product.store_id == uuid.UUID(store_id),
            Product.status == "active",
        )
        count_result = await session.execute(count_stmt)
        total = count_result.scalar_one()

        products = []
        for product, category_name in rows:
            products.append(
                StoreProductItem(
                    id=str(product.id),
                    name=product.name,
                    description=product.description,
                    price=float(product.price) if product.price else None,
                    stock=product.stock,
                    unit=product.unit,
                    images=product.images,
                    shelf_location=product.shelf_location,
                    category_name=category_name,
                )
            )

        return StoreProductsResponse(
            products=products, page=page, limit=limit, total=total
        )


@router.post("/register", response_model=StoreRegisterResponse)
async def register_store(data: StoreRegisterRequest):
    async with async_session() as session:
        store = Store(
            id=uuid.uuid4(),
            name=data.name,
            address=data.address,
            latitude=data.latitude,
            longitude=data.longitude,
            phone=data.phone,
            email=data.email,
            zalo=data.zalo,
            industry=data.industry,
            status="pending",
            location_verified=False,
        )
        session.add(store)
        await session.commit()

        return StoreRegisterResponse(id=str(store.id), status=store.status)


@router.post("/validate-location", response_model=ValidateLocationResponse)
async def validate_location(data: ValidateLocationRequest):
    if not (-90 <= data.lat <= 90):
        return ValidateLocationResponse(
            valid=False, message="Latitude must be between -90 and 90"
        )
    if not (-180 <= data.lng <= 180):
        return ValidateLocationResponse(
            valid=False, message="Longitude must be between -180 and 180"
        )
    return ValidateLocationResponse(valid=True, message="Location is valid")
