import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.database import async_session
from src.models.store import Category, Product, Store

router = APIRouter(prefix="/api/products", tags=["Products"])


class StoreInfo(BaseModel):
    id: str
    name: str
    address: str
    phone: str | None = None
    latitude: float
    longitude: float
    model_config = {"from_attributes": True}


class ProductDetailResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    price: float | None = None
    stock: int | None = None
    unit: str | None = None
    weight_grams: int | None = None
    dimensions: dict | None = None
    barcode: str | None = None
    brand: str | None = None
    images: list[str] | None = None
    shelf_location: str | None = None
    category_name: str | None = None
    status: str | None = None
    store: StoreInfo
    model_config = {"from_attributes": True}


class AlternativeProductItem(BaseModel):
    id: str
    name: str
    price: float | None = None
    stock: int | None = None
    store_name: str | None = None
    model_config = {"from_attributes": True}


class AlternativesResponse(BaseModel):
    alternatives: list[AlternativeProductItem]


@router.get("/{product_id}", response_model=ProductDetailResponse)
async def get_product_detail(product_id: str):
    async with async_session() as session:
        stmt = (
            select(Product, Category.name.label("category_name"))
            .outerjoin(Category, Product.category_id == Category.id)
            .options(selectinload(Product.store))
            .where(Product.id == uuid.UUID(product_id))
        )
        result = await session.execute(stmt)
        row = result.one_or_none()

        if not row:
            raise HTTPException(status_code=404, detail="Product not found")

        product, category_name = row
        store = product.store

        return ProductDetailResponse(
            id=str(product.id),
            name=product.name,
            description=product.description,
            price=float(product.price) if product.price else None,
            stock=product.stock,
            unit=product.unit,
            weight_grams=product.weight_grams,
            dimensions=product.dimensions,
            barcode=product.barcode,
            brand=product.brand,
            images=product.images,
            shelf_location=product.shelf_location,
            category_name=category_name,
            status=product.status,
            store=StoreInfo(
                id=str(store.id),
                name=store.name,
                address=store.address,
                phone=store.phone,
                latitude=store.latitude,
                longitude=store.longitude,
            ),
        )


@router.get("/{product_id}/alternatives", response_model=AlternativesResponse)
async def get_alternatives(product_id: str, limit: int = 10):
    async with async_session() as session:
        # Get the product to find its category
        product_stmt = select(Product).where(Product.id == uuid.UUID(product_id))
        product_result = await session.execute(product_stmt)
        product = product_result.scalar_one_or_none()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        if not product.category_id:
            return AlternativesResponse(alternatives=[])

        # Find similar products in the same category, excluding the current product
        stmt = (
            select(Product, Store.name.label("store_name"))
            .join(Store, Product.store_id == Store.id)
            .where(Product.category_id == product.category_id)
            .where(Product.id != uuid.UUID(product_id))
            .where(Product.status == "active")
            .where(Product.stock > 0)
            .limit(limit)
        )
        result = await session.execute(stmt)
        rows = result.all()

        alternatives = [
            AlternativeProductItem(
                id=str(p.id),
                name=p.name,
                price=float(p.price) if p.price else None,
                stock=p.stock,
                store_name=store_name,
            )
            for p, store_name in rows
        ]

        return AlternativesResponse(alternatives=alternatives)
