import uuid
import io
import csv
from typing import List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy import select, func, delete

from src.database import async_session
from src.models.store import Product, Store, Category

router = APIRouter(prefix="/api/owner", tags=["Owner"])


class OwnerProductItem(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    stock: int
    unit: str
    barcode: Optional[str] = None
    brand: Optional[str] = None
    shelf_location: Optional[str] = None
    status: str
    created_at: Optional[str] = None
    model_config = {"from_attributes": True}


class OwnerProductListResponse(BaseModel):
    products: List[OwnerProductItem]
    total: int
    page: int
    limit: int


class CreateProductRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    stock: int = Field(default=0, ge=0)
    unit: str = Field(default="cai")
    weight_grams: Optional[int] = None
    barcode: Optional[str] = None
    brand: Optional[str] = None
    shelf_location: Optional[str] = None
    category_id: Optional[str] = None


class UpdateProductRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    stock: Optional[int] = Field(None, ge=0)
    unit: Optional[str] = None
    barcode: Optional[str] = None
    brand: Optional[str] = None
    shelf_location: Optional[str] = None
    status: Optional[str] = None


class BulkUploadResponse(BaseModel):
    uploaded: int
    errors: List[str]
    message: str


class AnalyticsSummaryResponse(BaseModel):
    store_id: str
    total_products: int
    total_orders: int
    total_revenue: float
    low_stock_count: int


@router.get("/products", response_model=OwnerProductListResponse)
async def owner_list_products(
    store_id: str,
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = None,
):
    async with async_session() as session:
        # Verify store exists
        store_stmt = select(Store).where(Store.id == uuid.UUID(store_id))
        store_result = await session.execute(store_stmt)
        store = store_result.scalar_one_or_none()
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")

        # Build query
        stmt = select(Product).where(Product.store_id == uuid.UUID(store_id))
        count_stmt = select(func.count(Product.id)).where(
            Product.store_id == uuid.UUID(store_id)
        )

        if search:
            stmt = stmt.where(Product.name.ilike(f"%{search}%"))
            count_stmt = count_stmt.where(Product.name.ilike(f"%{search}%"))

        # Pagination
        offset = (page - 1) * limit
        stmt = stmt.offset(offset).limit(limit).order_by(Product.created_at.desc())

        result = await session.execute(stmt)
        products = result.scalars().all()

        count_result = await session.execute(count_stmt)
        total = count_result.scalar_one()

        items = [
            OwnerProductItem(
                id=str(p.id),
                name=p.name,
                description=p.description,
                price=float(p.price) if p.price else None,
                stock=p.stock,
                unit=p.unit or "cai",
                barcode=p.barcode,
                brand=p.brand,
                shelf_location=p.shelf_location,
                status=p.status,
                created_at=p.created_at,
            )
            for p in products
        ]

        return OwnerProductListResponse(
            products=items, total=total, page=page, limit=limit
        )


@router.post("/products")
async def owner_create_product(data: CreateProductRequest, store_id: str):
    async with async_session() as session:
        product = Product(
            id=uuid.uuid4(),
            store_id=uuid.UUID(store_id),
            name=data.name,
            description=data.description,
            price=data.price,
            stock=data.stock,
            unit=data.unit,
            weight_grams=data.weight_grams,
            barcode=data.barcode,
            brand=data.brand,
            shelf_location=data.shelf_location,
            category_id=uuid.UUID(data.category_id) if data.category_id else None,
            status="active",
        )
        session.add(product)
        await session.commit()

        return {
            "id": str(product.id),
            "status": "created",
            "message": "Product created successfully",
        }


@router.put("/products/{product_id}")
async def owner_update_product(
    product_id: str, data: UpdateProductRequest, store_id: str
):
    async with async_session() as session:
        stmt = select(Product).where(
            Product.id == uuid.UUID(product_id),
            Product.store_id == uuid.UUID(store_id),
        )
        result = await session.execute(stmt)
        product = result.scalar_one_or_none()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        if data.name is not None:
            product.name = data.name
        if data.description is not None:
            product.description = data.description
        if data.price is not None:
            product.price = data.price
        if data.stock is not None:
            product.stock = data.stock
        if data.unit is not None:
            product.unit = data.unit
        if data.barcode is not None:
            product.barcode = data.barcode
        if data.brand is not None:
            product.brand = data.brand
        if data.shelf_location is not None:
            product.shelf_location = data.shelf_location
        if data.status is not None:
            product.status = data.status

        await session.commit()
        return {
            "id": product_id,
            "status": "updated",
            "message": "Product updated successfully",
        }


@router.delete("/products/{product_id}")
async def owner_delete_product(product_id: str, store_id: str):
    async with async_session() as session:
        stmt = select(Product).where(
            Product.id == uuid.UUID(product_id),
            Product.store_id == uuid.UUID(store_id),
        )
        result = await session.execute(stmt)
        product = result.scalar_one_or_none()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        await session.delete(product)
        await session.commit()

        return {
            "id": product_id,
            "status": "deleted",
            "message": "Product deleted successfully",
        }


@router.post("/products/bulk-upload")
async def owner_bulk_upload(store_id: str, file: UploadFile = File(...)):
    async with async_session() as session:
        content = await file.read()
        decoded = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(decoded))

        uploaded = 0
        errors = []

        for row_num, row in enumerate(reader, start=2):
            try:
                name = row.get("name", "").strip()
                if not name:
                    errors.append(f"Row {row_num}: Missing name")
                    continue

                price_str = row.get("price", "0").strip()
                try:
                    price = float(price_str)
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid price '{price_str}'")
                    continue

                stock_str = row.get("stock", "0").strip()
                try:
                    stock = int(stock_str)
                except ValueError:
                    stock = 0

                product = Product(
                    id=uuid.uuid4(),
                    store_id=uuid.UUID(store_id),
                    name=name,
                    description=row.get("description", ""),
                    price=price,
                    stock=stock,
                    unit=row.get("unit", "cai"),
                    barcode=row.get("barcode", ""),
                    brand=row.get("brand", ""),
                    shelf_location=row.get("shelf_location", ""),
                    status="active",
                )
                session.add(product)
                uploaded += 1

            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")

        await session.commit()

        return BulkUploadResponse(
            uploaded=uploaded,
            errors=errors,
            message=f"Successfully uploaded {uploaded} products",
        )


@router.get("/analytics/summary")
async def owner_analytics_summary(store_id: str):
    async with async_session() as session:
        # Count products
        products_stmt = select(func.count(Product.id)).where(
            Product.store_id == uuid.UUID(store_id)
        )
        products_result = await session.execute(products_stmt)
        total_products = products_result.scalar_one()

        # Count low stock
        low_stock_stmt = select(func.count(Product.id)).where(
            Product.store_id == uuid.UUID(store_id),
            Product.stock < 10,
        )
        low_stock_result = await session.execute(low_stock_stmt)
        low_stock_count = low_stock_result.scalar_one()

        # Mock orders data (would come from Order model in full implementation)
        total_orders = 0
        total_revenue = 0.0

        return AnalyticsSummaryResponse(
            store_id=store_id,
            total_products=total_products,
            total_orders=total_orders,
            total_revenue=total_revenue,
            low_stock_count=low_stock_count,
        )
