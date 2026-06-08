"""
Favorite/Wishlist model for VietStore RAG.

Users can save products to their favorites list for quick access.
"""

from sqlalchemy import Column, ForeignKey, Index, String, UniqueConstraint, DateTime, func as sa_func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from src.database import Base


class Favorite(Base):
    """A user's favorite/wishlist item."""

    __tablename__ = "favorites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    product_id = Column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime, server_default=sa_func.now())

    # Relationships
    user = relationship("User", backref="favorites")
    product = relationship("Product", backref="favorited_by")

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_favorite_user_product"),
        Index("idx_favorite_user_id", "user_id"),
        Index("idx_favorite_product_id", "product_id"),
    )
