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
    Index,
    DateTime,
    func as sa_func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from src.database import Base


class Cart(Base):
    __tablename__ = "carts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"))
    status = Column(String(20), default="active")
    created_at = Column(DateTime, server_default=sa_func.now())
    updated_at = Column(DateTime, server_default=sa_func.now(), onupdate=sa_func.now())


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cart_id = Column(UUID(as_uuid=True), ForeignKey("carts.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"))
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(DECIMAL(12, 2), nullable=False)
    created_at = Column(DateTime, server_default=sa_func.now())


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number = Column(String(20), unique=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"))
    delivery_method = Column(String(20))
    delivery_address = Column(Text)
    delivery_lat = Column(DECIMAL(9, 6))
    delivery_lng = Column(DECIMAL(9, 6))
    subtotal = Column(DECIMAL(12, 2))
    shipping_fee = Column(DECIMAL(12, 2), default=0)
    discount = Column(DECIMAL(12, 2), default=0)
    total_amount = Column(DECIMAL(12, 2))
    payment_method = Column(String(20))
    payment_status = Column(String(20), default="pending")
    status = Column(String(20), default="pending")
    confirmed_at = Column(String)
    completed_at = Column(String)
    created_at = Column(DateTime, server_default=sa_func.now())

    items = relationship("OrderItem", back_populates="order", lazy="selectin")
    payments = relationship("PaymentTransaction", back_populates="order")

    __table_args__ = (
        Index("idx_order_user_id", "user_id"),
        Index("idx_order_store_id", "store_id"),
        Index("idx_order_status", "status"),
        Index("idx_order_number", "order_number"),
        Index("idx_order_created_at", "created_at"),
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(DECIMAL(12, 2), nullable=False)
    subtotal = Column(DECIMAL(12, 2), nullable=False)

    order = relationship("Order", back_populates="items")


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    name = Column(String(100))
    sku = Column(String(50))
    price = Column(DECIMAL(12, 2))
    stock = Column(Integer, default=0)
    attributes = Column(JSON)
