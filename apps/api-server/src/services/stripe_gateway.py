"""
Stripe Payment Gateway Wrapper

Wrap existing StripeService from services/stripe.py
to implement the PaymentGateway abstract interface.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from src.services.payment_base import PaymentGateway, PaymentResult, RefundResult
from src.services.stripe import get_stripe_service

logger = logging.getLogger(__name__)


class StripeGateway(PaymentGateway):
    """Cong thanh toan Stripe - wrapper cho StripeService hien co."""

    def __init__(self) -> None:
        self._service = get_stripe_service()

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
        """Tao Stripe PaymentIntent."""
        try:
            if not self._service.is_ready():
                return PaymentResult(success=False, message="Stripe chua duoc cau hinh")

            meta = metadata or {}
            meta["order_id"] = order_id
            meta["description"] = description

            # Stripe amount = smallest currency unit (cents for USD, whole VND)
            amount_int = int(amount)

            result = await self._service.create_payment_intent(
                amount=amount_int,
                currency=currency,
                metadata=meta,
            )

            if not result:
                return PaymentResult(success=False, message="Tao PaymentIntent that bai")

            return PaymentResult(
                success=True,
                message="Tao PaymentIntent thanh cong",
                transaction_id=result["id"],
                gateway_url=None,  # Stripe dung client_secret tren frontend
                raw_response=result,
            )

        except Exception as e:
            logger.exception("Stripe create_payment error: %s", e)
            return PaymentResult(success=False, message=f"Loi tao thanh toan Stripe: {e}")

    async def verify_payment(self, query_params: dict[str, Any]) -> PaymentResult:
        """Xac minh thanh toan Stripe qua payment_intent_id."""
        try:
            payment_intent_id = str(query_params.get("payment_intent", ""))
            if not payment_intent_id:
                return PaymentResult(success=False, message="Thieu payment_intent")

            if not self._service.is_ready():
                return PaymentResult(success=False, message="Stripe chua duoc cau hinh")

            result = await self._service.get_payment_intent(payment_intent_id)
            if not result:
                return PaymentResult(success=False, message="Khong tim thay PaymentIntent")

            is_success = result.get("status") == "succeeded"
            return PaymentResult(
                success=is_success,
                message="Thanh toan thanh cong" if is_success else f"Trang thai: {result.get('status')}",
                transaction_id=payment_intent_id,
                raw_response=result,
            )

        except Exception as e:
            logger.exception("Stripe verify_payment error: %s", e)
            return PaymentResult(success=False, message=f"Loi xac minh Stripe: {e}")

    async def process_webhook(
        self, payload: bytes | str, headers: dict[str, Any]
    ) -> PaymentResult:
        """Xu ly webhook Stripe."""
        try:
            if isinstance(payload, bytes):
                body = payload.decode("utf-8")
            else:
                body = payload

            event = json.loads(body)
            event_type = event.get("type", "")
            obj = event.get("data", {}).get("object", {})
            payment_intent_id = obj.get("id", "")
            status = obj.get("status", "")

            is_success = event_type == "payment_intent.succeeded" or status == "succeeded"

            return PaymentResult(
                success=is_success,
                message=f"Webhook Stripe: {event_type}",
                transaction_id=payment_intent_id,
                raw_response=event,
            )

        except Exception as e:
            logger.exception("Stripe process_webhook error: %s", e)
            return PaymentResult(success=False, message=f"Loi xu ly webhook Stripe: {e}")

    async def refund(
        self,
        transaction_id: str,
        amount: float | None = None,
        reason: str | None = None,
    ) -> RefundResult:
        """Hoan tien Stripe."""
        try:
            if not self._service.is_ready():
                return RefundResult(success=False, message="Stripe chua duoc cau hinh")

            amount_int = int(amount) if amount else None
            result = await self._service.refund_payment(
                payment_intent_id=transaction_id,
                amount=amount_int,
            )

            if not result:
                return RefundResult(success=False, message="Hoan tien Stripe that bai")

            return RefundResult(
                success=True,
                message="Hoan tien thanh cong",
                refund_id=result.get("id"),
                raw_response=result,
            )

        except Exception as e:
            logger.exception("Stripe refund error: %s", e)
            return RefundResult(success=False, message=f"Loi hoan tien Stripe: {e}")

    async def get_status(self, transaction_id: str) -> dict[str, Any]:
        """Lay trang thai PaymentIntent Stripe."""
        try:
            if not self._service.is_ready():
                return {"status": "error", "message": "Stripe chua duoc cau hinh"}

            result = await self._service.get_payment_intent(transaction_id)
            if not result:
                return {"status": "error", "message": "Khong tim thay PaymentIntent"}

            return {"status": result.get("status"), "data": result}

        except Exception as e:
            logger.exception("Stripe get_status error: %s", e)
            return {"status": "error", "message": str(e)}
