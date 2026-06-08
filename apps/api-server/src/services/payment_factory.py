"""
Payment Gateway Factory

Cung cap factory pattern de lay cong thanh toan theo ten.
Ho tro Stripe, VNPay, MoMo, ZaloPay va COD.
"""

from __future__ import annotations

import logging
from typing import Any

from src.services.payment_base import PaymentGateway, PaymentResult, RefundResult

logger = logging.getLogger(__name__)


class CODGateway(PaymentGateway):
    """Cong thanh toan COD (Cash on Delivery) - khong can xu ly online."""

    async def create_payment(
        self,
        order_id: str,
        amount: float,
        currency: str,
        description: str,
        return_url: str,
        cancel_url: str,
        metadata: dict[str, Any] | None = None,
    ) -> PaymentResult:
        """COD khong can tao URL thanh toan."""
        return PaymentResult(
            success=True,
            message="COD: Don hang duoc ghi nhan, thanh toan khi nhan hang",
            transaction_id=order_id,
            gateway_url=None,
        )

    async def verify_payment(self, query_params: dict[str, Any]) -> PaymentResult:
        """COD luon thanh cong."""
        order_id = str(query_params.get("order_id", ""))
        return PaymentResult(
            success=True,
            message="COD: Xac nhan thanh cong",
            transaction_id=order_id,
        )

    async def process_webhook(
        self, payload: bytes | str, headers: dict[str, Any]
    ) -> PaymentResult:
        """COD khong co webhook."""
        return PaymentResult(
            success=True,
            message="COD: Khong co webhook",
        )

    async def refund(
        self,
        transaction_id: str,
        amount: float | None = None,
        reason: str | None = None,
    ) -> RefundResult:
        """COD khong hoan tien qua cong."""
        return RefundResult(
            success=False,
            message="COD: Hoan tien thu cong tai quay",
        )

    async def get_status(self, transaction_id: str) -> dict[str, Any]:
        """Trang thai COD luon pending/success."""
        return {"status": "pending", "message": "COD: Cho giao hang va thu tien"}


class PaymentGatewayFactory:
    """Factory tao instance cong thanh toan."""

    GATEWAYS: dict[str, type[PaymentGateway]] = {}

    @classmethod
    def _lazy_load(cls) -> None:
        """Lazy import cac gateway de tranh circular import."""
        if cls.GATEWAYS:
            return

        from src.services.stripe_gateway import StripeGateway
        from src.services.vnpay_gateway import VNPayGateway
        from src.services.momo_gateway import MoMoGateway
        from src.services.zalopay_gateway import ZaloPayGateway

        cls.GATEWAYS = {
            "stripe": StripeGateway,
            "vnpay": VNPayGateway,
            "momo": MoMoGateway,
            "zalopay": ZaloPayGateway,
            "cod": CODGateway,
        }

    @classmethod
    def get_gateway(cls, name: str) -> PaymentGateway:
        """
        Lay instance cong thanh toan theo ten.

        Args:
            name: Ten cong thanh toan (stripe, vnpay, momo, zalopay, cod)

        Returns:
            Instance PaymentGateway tuong ung

        Raises:
            ValueError: Neu cong thanh toan khong duoc ho tro
        """
        cls._lazy_load()
        gateway_name = name.lower().strip()
        gateway_cls = cls.GATEWAYS.get(gateway_name)
        if not gateway_cls:
            supported = ", ".join(cls.GATEWAYS.keys())
            raise ValueError(f"Cong thanh toan '{name}' khong duoc ho tro. Ho tro: {supported}")
        return gateway_cls()

    @classmethod
    def list_gateways(cls) -> list[str]:
        """Tra ve danh sach ten cong thanh toan duoc ho tro."""
        cls._lazy_load()
        return list(cls.GATEWAYS.keys())
