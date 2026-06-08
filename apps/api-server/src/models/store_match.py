"""
Store Match Model

Stores potential matches between unverified registered stores
and existing verified stores (seed data).
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database import Base


class StoreMatch(Base):
    """Potential match between a registered store and a seed store."""

    __tablename__ = "store_matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    seed_store_id = Column(
        UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
    )
    registered_store_id = Column(
        UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
    )

    # How similar the two stores are (0.0 - 1.0)
    similarity_score = Column(Numeric(5, 4), nullable=False)

    # Which fields triggered the match
    matched_fields = Column(JSON, nullable=True)
    # e.g. ["name", "address", "phone"]

    # Status of the match
    status = Column(
        String(20),
        nullable=False,
        default="pending",
    )
    # pending, approved, rejected

    reviewed_by_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    seed_store = relationship(
        "Store",
        foreign_keys=[seed_store_id],
        backref="seed_matches",
    )
    registered_store = relationship(
        "Store",
        foreign_keys=[registered_store_id],
        backref="registration_matches",
    )
    reviewed_by = relationship("User", backref="reviewed_matches")

    __table_args__ = (
        Index("idx_match_status", "status"),
        Index("idx_match_registered", "registered_store_id", "status"),
    )

    def __repr__(self):
        return (
            f"<StoreMatch(id={self.id}, similarity={self.similarity_score}, "
            f"status={self.status})>"
        )
