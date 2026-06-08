from sqlalchemy import (
    Column,
    String,
    Text,
    ForeignKey,
    JSON,
    Index,
    DateTime,
    func as sa_func,
)
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(20), nullable=False)  # store, product, user, order
    target_id = Column(UUID(as_uuid=True), nullable=False)
    target_name = Column(String(200))
    reporter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    reporter_name = Column(String(100))
    reason = Column(String(50), nullable=False)  # fake_products, wrong_price, harassment, scam, spam, inappropriate
    description = Column(Text, nullable=False)
    status = Column(String(20), default="pending")  # pending, reviewed, resolved, dismissed
    evidence = Column(JSON)  # Array of file URLs
    resolution_notes = Column(Text)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, server_default=sa_func.now())
    updated_at = Column(DateTime, server_default=sa_func.now(), onupdate=sa_func.now())

    __table_args__ = (
        Index("idx_report_type", "type"),
        Index("idx_report_status", "status"),
        Index("idx_report_target", "target_id"),
        Index("idx_report_reporter", "reporter_id"),
    )
