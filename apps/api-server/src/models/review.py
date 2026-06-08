from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    Boolean,
    JSON,
    ForeignKey,
    CheckConstraint,
    DateTime,
    func as sa_func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from src.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))
    rating = Column(Integer, nullable=False)
    title = Column(String(200))
    content = Column(Text)
    images = Column(JSON)  # Changed from ARRAY(String) to JSON for SQLite compatibility
    is_verified_purchase = Column(Boolean, default=False)
    helpful_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=sa_func.now())
    updated_at = Column(DateTime, server_default=sa_func.now(), onupdate=sa_func.now())

    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="check_rating_range"),
    )
