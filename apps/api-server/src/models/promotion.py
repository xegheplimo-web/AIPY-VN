from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DECIMAL,
    Text,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.database import Base


class Promotion(Base):
    __tablename__ = "promotions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    type = Column(String(20), nullable=False)  # percentage, fixed, free_shipping
    value = Column(DECIMAL(12, 2))  # Percentage value or fixed amount
    min_order_amount = Column(DECIMAL(12, 2), default=0)
    max_discount = Column(DECIMAL(12, 2))
    usage_limit = Column(Integer)  # null = unlimited
    used_count = Column(Integer, default=0)
    start_date = Column(String, nullable=False)
    end_date = Column(String, nullable=False)
    status = Column(String(20), default="active")  # active, expired, scheduled, paused
    applicable_stores = Column(JSON)  # ["all"] or ["store_id1", "store_id2"]
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(String, default="now()")
    updated_at = Column(String, default="now()")

    __table_args__ = (
        Index("idx_promotion_code", "code"),
        Index("idx_promotion_status", "status"),
        Index("idx_promotion_dates", "start_date", "end_date"),
    )
