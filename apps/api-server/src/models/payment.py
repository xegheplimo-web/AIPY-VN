"""
Payment Transaction Model

Stores all payment transactions regardless of gateway.
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
    Text,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database import Base


class PaymentTransaction(Base):
    """Payment transaction record for all gateways."""

    __tablename__ = "payment_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Gateway info
    gateway = Column(String(20), nullable=False, index=True)
    # stripe, vnpay, momo, zalopay, cod

    gateway_transaction_id = Column(String(255), nullable=True, index=True)
    # Transaction ID from the gateway (e.g., Stripe payment_intent.id, VNPay txnRef)

    # Amount
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="VND")

    # Status
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )
    # pending, processing, success, failed, refunded, cancelled

    # Raw data for audit
    request_data = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)
    webhook_data = Column(JSON, nullable=True)

    # Refund info
    refunded_amount = Column(Numeric(12, 2), nullable=True)
    refund_reason = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    order = relationship("Order", back_populates="payments")
    user = relationship("User", backref="payment_transactions")

    __table_args__ = (
        Index("idx_payment_order_gateway", "order_id", "gateway"),
        Index("idx_payment_status_gateway", "status", "gateway"),
    )

    def __repr__(self):
        return (
            f"<PaymentTransaction(id={self.id}, gateway={self.gateway}, "
            f"amount={self.amount}, status={self.status})>"
        )
