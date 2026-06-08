"""
MoMo Payment Gateway Integration

Tich hop cong thanh toan MoMo.
Su dung HMAC-SHA256 de ky va xac minh chu ky.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import uuid
from typing import Any

import httpx

from src.config import config
from src.services.payment_base import PaymentGateway, PaymentResult, RefundResult

logger = logging.getLogger(__name__)


class MoMoGateway(PaymentGateway):
    """Cong thanh toan MoMo."""

    def __init__(self) -> None:
        self.cfg = config.momo

    def _get_config_attr(self, name: str) -> str:
        """Lay thuoc tinh config."""
        if hasattr(self.cfg, name):
            return getattr(self.cfg, name) or ""
        return ""

    def _generate_signature(self, raw_data: str, secret: str) -> str:
        """Tao chu ky HMAC-SHA256 cho MoMo."""
        signed = hmac.new(secret.encode("utf-8"), raw_data.encode("utf-8"), hashlib.sha256).hexdigest()
        return signed

    def _build_raw_signature(self, data: dict[str, Any]) -> str:
        """Xay dung chuoi raw de ky theo thu tu MoMo yeu cau."""
        # Thu tu tieu chuan: accessKey + amount + extraData + ipnUrl + orderId + orderInfo + partnerCode + redirectUrl + requestId + requestType
        access_key = str(data.get("accessKey", ""))
        amount = str(data.get("amount", ""))
        extra_data = str(data.get("extraData", ""))
        ipn_url = str(data.get("ipnUrl", ""))
        order_id = str(data.get("orderId", ""))
        order_info = str(data.get("orderInfo", ""))
        partner_code = str(data.get("partnerCode", ""))
        redirect_url = str(data.get("redirectUrl", ""))
        request_id = str(data.get("requestId", ""))
        request_type = str(data.get("requestType", ""))
        raw = f"accessKey={access_key}&amount={amount}&extraData={extra_data}&ipnUrl={ipn_url}&orderId={order_id}&orderInfo={order_info}&partnerCode={partner_code}&redirectUrl={redirect_url}&requestId={request_id}&requestType={request_type}"
        return raw

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
        """Tao yeu cau thanh toan MoMo."""
        try:
            partner_code = self._get_config_attr("partner_code")
            access_key = self._get_config_attr("access_key")
            secret_key = self._get_config_attr("secret_key")
            endpoint = self._get_config_attr("endpoint")
            notify_url = self._get_config_attr("notify_url")

            if not all([partner_code, access_key, secret_key, endpoint]):
                logger.error("MoMo config missing")
                return PaymentResult(success=False, message="MoMo chua duoc cau hinh")

            request_id = str(uuid.uuid4())
            extra_data = metadata.get("extraData", "") if metadata else ""
            order_info = description or f"Thanh toan don hang {order_id}"

            payload: dict[str, Any] = {
                "partnerCode": partner_code,
                "accessKey": access_key,
                "requestId": request_id,
                "amount": str(int(amount)),
                "orderId": order_id,
                "orderInfo": order_info,
                "redirectUrl": return_url,
                "ipnUrl": notify_url or return_url,
                "extraData": extra_data,
                "requestType": "captureWallet",
                "lang": "vi",
            }

            raw_signature = self._build_raw_signature(payload)
            signature = self._generate_signature(raw_signature, secret_key)
            payload["signature"] = signature

            async with httpx.AsyncClient() as client:
                response = await client.post(endpoint, json=payload, timeout=30)
                response.raise_for_status()
                result = response.json()

            if result.get("resultCode") == 0:
                return PaymentResult(
                    success=True,
                    message="Tao thanh toan MoMo thanh cong",
                    transaction_id=order_id,
                    gateway_url=result.get("payUrl"),
                    raw_response=result,
                )
            else:
                return PaymentResult(
                    success=False,
                    message=f"MoMo loi: {result.get('message', 'Unknown')}",
                    transaction_id=order_id,
                    raw_response=result,
                )

        except Exception as e:
            logger.exception("MoMo create_payment error: %s", e)
            return PaymentResult(success=False, message=f"Loi tao thanh toan MoMo: {e}")

    async def verify_payment(self, query_params: dict[str, Any]) -> PaymentResult:
        """Xac minh ket qua tra ve tu MoMo (callback URL)."""
        try:
            secret_key = self._get_config_attr("secret_key")
            received_sig = str(query_params.get("signature", ""))

            if not received_sig:
                return PaymentResult(success=False, message="Thieu chu ky MoMo")

            # Rebuild raw string tu callback params
            raw = self._build_raw_signature(query_params)
            expected = self._generate_signature(raw, secret_key)

            if not hmac.compare_digest(expected.lower(), received_sig.lower()):
                return PaymentResult(success=False, message="Chu ky MoMo khong hop le")

            result_code = query_params.get("resultCode")
            is_success = str(result_code) == "0"
            order_id = str(query_params.get("orderId", ""))

            return PaymentResult(
                success=is_success,
                message="Giao dich thanh cong" if is_success else f"Giao dich that bai (code={result_code})",
                transaction_id=order_id,
                raw_response=dict(query_params),
            )

        except Exception as e:
            logger.exception("MoMo verify_payment error: %s", e)
            return PaymentResult(success=False, message=f"Loi xac minh MoMo: {e}")

    async def process_webhook(
        self, payload: bytes | str, headers: dict[str, Any]
    ) -> PaymentResult:
        """Xu ly webhook/IPN tu MoMo."""
        try:
            if isinstance(payload, bytes):
                body = payload.decode("utf-8")
            else:
                body = payload

            data = json.loads(body) if body.startswith("{") else {"signature": ""}
            return await self.verify_payment(data)

        except Exception as e:
            logger.exception("MoMo process_webhook error: %s", e)
            return PaymentResult(success=False, message=f"Loi xu ly webhook MoMo: {e}")

    async def refund(
        self,
        transaction_id: str,
        amount: float | None = None,
        reason: str | None = None,
    ) -> RefundResult:
        """Hoan tien MoMo (stub)."""
        logger.warning("MoMo refund chua duoc trien khai")
        return RefundResult(
            success=False,
            message="MoMo refund chua duoc trien khai",
            refund_id=None,
        )

    async def get_status(self, transaction_id: str) -> dict[str, Any]:
        """Lay trang thai giao dich MoMo."""
        return {"status": "unknown", "message": "MoMo get_status chua duoc trien khai"}
