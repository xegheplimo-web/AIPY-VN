"""
ZaloPay Payment Gateway Integration

Tich hop cong thanh toan ZaloPay.
Su dung HMAC-SHA256 de ky va xac minh chu ky (mac).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from typing import Any

import httpx

from src.config import config
from src.services.payment_base import PaymentGateway, PaymentResult, RefundResult

logger = logging.getLogger(__name__)


class ZaloPayGateway(PaymentGateway):
    """Cong thanh toan ZaloPay."""

    def __init__(self) -> None:
        self.cfg = config.zalopay

    def _get_config_attr(self, name: str) -> str:
        """Lay thuoc tinh config."""
        if hasattr(self.cfg, name):
            return getattr(self.cfg, name) or ""
        return ""

    def _generate_mac(self, data: str, key: str) -> str:
        """Tao chu ky HMAC-SHA256 cho ZaloPay."""
        signed = hmac.new(key.encode("utf-8"), data.encode("utf-8"), hashlib.sha256).hexdigest()
        return signed

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
        """Tao yeu cau thanh toan ZaloPay."""
        try:
            app_id = self._get_config_attr("app_id")
            key1 = self._get_config_attr("key1")
            key2 = self._get_config_attr("key2")
            endpoint = self._get_config_attr("endpoint")
            callback_url = self._get_config_attr("notify_url")

            if not all([app_id, key1, endpoint]):
                logger.error("ZaloPay config missing")
                return PaymentResult(success=False, message="ZaloPay chua duoc cau hinh")

            app_time = int(time.time() * 1000)
            app_trans_id = metadata.get("app_trans_id", order_id) if metadata else order_id
            app_user = metadata.get("app_user", "user") if metadata else "user"
            embed_data = json.dumps({"redirecturl": return_url})
            item = json.dumps(metadata.get("items", []) if metadata else [])

            # Build data string for MAC: app_id|app_trans_id|app_user|amount|app_time|embed_data|item
            data_str = f"{app_id}|{app_trans_id}|{app_user}|{int(amount)}|{app_time}|{embed_data}|{item}"
            mac = self._generate_mac(data_str, key1)

            payload: dict[str, Any] = {
                "app_id": int(app_id),
                "app_trans_id": app_trans_id,
                "app_time": app_time,
                "app_user": app_user,
                "amount": int(amount),
                "item": item,
                "description": description or f"Thanh toan don hang {order_id}",
                "embed_data": embed_data,
                "bank_code": "",
                "callback_url": callback_url or "",
                "mac": mac,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(endpoint, json=payload, timeout=30)
                response.raise_for_status()
                result = response.json()

            if result.get("return_code") == 1:
                return PaymentResult(
                    success=True,
                    message="Tao thanh toan ZaloPay thanh cong",
                    transaction_id=app_trans_id,
                    gateway_url=result.get("order_url"),
                    raw_response=result,
                )
            else:
                return PaymentResult(
                    success=False,
                    message=f"ZaloPay loi: {result.get('return_message', 'Unknown')}",
                    transaction_id=app_trans_id,
                    raw_response=result,
                )

        except Exception as e:
            logger.exception("ZaloPay create_payment error: %s", e)
            return PaymentResult(success=False, message=f"Loi tao thanh toan ZaloPay: {e}")

    async def verify_payment(self, query_params: dict[str, Any]) -> PaymentResult:
        """Xac minh ket qua tra ve tu ZaloPay (callback URL)."""
        try:
            key2 = self._get_config_attr("key2") or self._get_config_attr("key1")
            received_mac = str(query_params.get("mac", ""))
            app_id = str(query_params.get("appid", ""))
            app_trans_id = str(query_params.get("apptransid", ""))
            amount = str(query_params.get("amount", ""))
            server_time = str(query_params.get("servertime", ""))

            if not received_mac:
                return PaymentResult(success=False, message="Thieu MAC ZaloPay")

            # ZaloPay callback mac = app_id|app_trans_id|amount|servertime
            data_str = f"{app_id}|{app_trans_id}|{amount}|{server_time}"
            expected = self._generate_mac(data_str, key2)

            if not hmac.compare_digest(expected.lower(), received_mac.lower()):
                return PaymentResult(success=False, message="MAC ZaloPay khong hop le")

            return_code = query_params.get("returncode", -1)
            is_success = str(return_code) == "1"

            return PaymentResult(
                success=is_success,
                message="Giao dich thanh cong" if is_success else f"Giao dich that bai (code={return_code})",
                transaction_id=app_trans_id,
                raw_response=dict(query_params),
            )

        except Exception as e:
            logger.exception("ZaloPay verify_payment error: %s", e)
            return PaymentResult(success=False, message=f"Loi xac minh ZaloPay: {e}")

    async def process_webhook(
        self, payload: bytes | str, headers: dict[str, Any]
    ) -> PaymentResult:
        """Xu ly webhook/IPN tu ZaloPay."""
        try:
            if isinstance(payload, bytes):
                body = payload.decode("utf-8")
            else:
                body = payload

            data = json.loads(body) if body.startswith("{") else {"mac": ""}
            return await self.verify_payment(data)

        except Exception as e:
            logger.exception("ZaloPay process_webhook error: %s", e)
            return PaymentResult(success=False, message=f"Loi xu ly webhook ZaloPay: {e}")

    async def refund(
        self,
        transaction_id: str,
        amount: float | None = None,
        reason: str | None = None,
    ) -> RefundResult:
        """Hoan tien ZaloPay (stub)."""
        logger.warning("ZaloPay refund chua duoc trien khai")
        return RefundResult(
            success=False,
            message="ZaloPay refund chua duoc trien khai",
            refund_id=None,
        )

    async def get_status(self, transaction_id: str) -> dict[str, Any]:
        """Lay trang thai giao dich ZaloPay."""
        return {"status": "unknown", "message": "ZaloPay get_status chua duoc trien khai"}
