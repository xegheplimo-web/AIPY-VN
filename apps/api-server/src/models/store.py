from sqlalchemy import (
    Column,
    String,
    Float,
    Boolean,
    JSON,
    Integer,
    DECIMAL,
    Text,
    ForeignKey,
    Table,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from src.db import Base


class Store(Base):
    __tablename__ = "stores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    address = Column(Text, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    phone = Column(String(20))
    email = Column(String(255))
    zalo = Column(String(20))
    logo_url = Column(String(500))
    cover_image_url = Column(String(500))
    images = Column(JSON)  # Changed from ARRAY(String) to JSON for SQLite compatibility
    business_hours = Column(JSON)
    is_open_now = Column(Boolean, default=True)
    rating = Column(DECIMAL(3, 2), default=0.00)
    total_reviews = Column(Integer, default=0)
    industry = Column(String(100))
    status = Column(String(20), default="active")
    location_verified = Column(Boolean, default=False)
    created_at = Column(String, default="now()")
    updated_at = Column(String, default="now()")

    products = relationship("Product", back_populates="store")

    __table_args__ = (
        Index("idx_store_status", "status"),
        Index("idx_store_location", "latitude", "longitude"),
        Index("idx_store_industry", "industry"),
        Index("idx_store_is_open", "is_open_now"),
    )


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"))
    name = Column(String(200), nullable=False)
    description = Column(Text)
    price = Column(DECIMAL(12, 2))
    stock = Column(Integer, default=0)
    unit = Column(String(50), default="cái")
    weight_grams = Column(Integer)
    dimensions = Column(JSON)
    barcode = Column(String(50))
    brand = Column(String(100))
    images = Column(JSON)  # Changed from ARRAY(String) to JSON for SQLite compatibility
    shelf_location = Column(String(100))
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))
    status = Column(String(20), default="active")
    created_at = Column(String, default="now()")
    updated_at = Column(String, default="now()")

    store = relationship("Store", back_populates="products")
    category = relationship("Category", back_populates="products")

    __table_args__ = (
        Index("idx_product_store_id", "store_id"),
        Index("idx_product_status", "status"),
        Index("idx_product_name", "name"),
        Index("idx_product_category", "category_id"),
        Index("idx_product_stock", "stock"),
    )


class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))
    icon_url = Column(String(500))
    description = Column(Text)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(String, default="now()")

    products = relationship("Product", back_populates="category")
