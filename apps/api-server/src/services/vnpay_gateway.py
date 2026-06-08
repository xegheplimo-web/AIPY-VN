"""
VNPay Payment Gateway v2.1.0 Integration

Tich hop cong thanh toan VNPay phien ban 2.1.0.
Su dung HMAC-SHA512 de ky va xac minh chu ky.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import urllib.parse
from datetime import datetime, timedelta
from typing import Any

import httpx

from src.config import config
from src.services.payment_base import PaymentGateway, PaymentResult, RefundResult

logger = logging.getLogger(__name__)


class VNPayGateway(PaymentGateway):
    """Cong thanh toan VNPay v2.1.0."""

    def __init__(self) -> None:
        self.cfg = config.vnpay

    def _get_config_attr(self, name: str) -> str:
        """Lay thuoc tinh config, ho tro ca snake_case va camelCase."""
        if hasattr(self.cfg, name):
            return getattr(self.cfg, name) or ""
        # Fallback snake_case
        snake_name = name
        if hasattr(self.cfg, snake_name):
            return getattr(self.cfg, snake_name) or ""
        return ""

    def _generate_signature(self, data: dict[str, Any], secret: str) -> str:
        """Tao chu ky HMAC-SHA512 cho VNPay."""
        # Loai bo cac key rong va vnp_SecureHash
        filtered = {k: v for k, v in data.items() if v not in (None, "") and k != "vnp_SecureHash"}
        # Sap xep theo key
        sorted_items = sorted(filtered.items())
        # Tao query string
        query_string = "&".join(f"{k}={urllib.parse.quote_plus(str(v))}" for k, v in sorted_items)
        # Ky
        signed = hmac.new(secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha512).hexdigest()
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
        """Tao yeu cau thanh toan VNPay."""
        try:
            tmn_code = self._get_config_attr("vnp_TmnCode")
            secret = self._get_config_attr("vnp_HashSecret")
            base_url = self._get_config_attr("vnp_Url")

            if not all([tmn_code, secret, base_url]):
                logger.error("VNPay config missing")
                return PaymentResult(success=False, message="VNPay chua duoc cau hinh")

            now = datetime.now()
            expire = now + timedelta(minutes=15)
            create_date = now.strftime("%Y%m%d%H%M%S")
            expire_date = expire.strftime("%Y%m%d%H%M%S")
            txn_ref = metadata.get("txn_ref", order_id) if metadata else order_id
            ip_addr = metadata.get("ip_addr", "127.0.0.1") if metadata else "127.0.0.1"

            params: dict[str, Any] = {
                "vnp_Version": "2.1.0",
                "vnp_Command": "pay",
                "vnp_TmnCode": tmn_code,
                "vnp_Amount": int(amount * 100),  # VNPay yeu cau nhan 100
                "vnp_CurrCode": currency.upper() if currency else "VND",
                "vnp_TxnRef": txn_ref,
                "vnp_OrderInfo": description or f"Thanh toan don hang {order_id}",
                "vnp_OrderType": "other",
                "vnp_Locale": "vn",
                "vnp_ReturnUrl": return_url,
                "vnp_IpAddr": ip_addr,
                "vnp_CreateDate": create_date,
                "vnp_ExpireDate": expire_date,
            }

            signature = self._generate_signature(params, secret)
            params["vnp_SecureHash"] = signature

            # Build URL
            query = "&".join(f"{k}={urllib.parse.quote_plus(str(v))}" for k, v in params.items())
            gateway_url = f"{base_url}?{query}"

            return PaymentResult(
                success=True,
                message="Tao URL thanh toan VNPay thanh cong",
                transaction_id=txn_ref,
                gateway_url=gateway_url,
                raw_response=params,
            )

        except Exception as e:
            logger.exception("VNPay create_payment error: %s", e)
            return PaymentResult(success=False, message=f"Loi tao thanh toan VNPay: {e}")

    async def verify_payment(self, query_params: dict[str, Any]) -> PaymentResult:
        """Xac minh ket qua tra ve tu VNPay (return URL)."""
        try:
            secret = self._get_config_attr("vnp_HashSecret")
            received_hash = str(query_params.get("vnp_SecureHash", ""))

            if not received_hash:
                return PaymentResult(success=False, message="Thieu chu ky VNPay")

            expected = self._generate_signature(query_params, secret)

            if not hmac.compare_digest(expected.lower(), received_hash.lower()):
                return PaymentResult(success=False, message="Chu ky VNPay khong hop le")

            status = str(query_params.get("vnp_ResponseCode", ""))
            txn_ref = str(query_params.get("vnp_TxnRef", ""))
            is_success = status == "00"

            return PaymentResult(
                success=is_success,
                message="Giao dich thanh cong" if is_success else f"Giao dich that bai (code={status})",
                transaction_id=txn_ref,
                raw_response=dict(query_params),
            )

        except Exception as e:
            logger.exception("VNPay verify_payment error: %s", e)
            return PaymentResult(success=False, message=f"Loi xac minh VNPay: {e}")

    async def process_webhook(
        self, payload: bytes | str, headers: dict[str, Any]
    ) -> PaymentResult:
        """Xu ly webhook/IPN tu VNPay."""
        try:
            # VNPay IPN gui duoi dang query params trong body
            if isinstance(payload, bytes):
                payload_str = payload.decode("utf-8")
            else:
                payload_str = payload

            # Parse query string
            params = dict(urllib.parse.parse_qsl(payload_str))
            # Hoac neu payload la dict/json
            if not params and isinstance(payload, bytes):
                import json
                try:
                    params = json.loads(payload.decode("utf-8"))
                except Exception:
                    params = {}

            return await self.verify_payment(params)

        except Exception as e:
            logger.exception("VNPay process_webhook error: %s", e)
            return PaymentResult(success=False, message=f"Loi xu ly webhook VNPay: {e}")

    async def refund(
        self,
        transaction_id: str,
        amount: float | None = None,
        reason: str | None = None,
    ) -> RefundResult:
        """Hoan tien qua API VNPay (tuy chon)."""
        # VNPay refund API yeu cau them thong tin nhu transaction_date, create_by, etc.
        # De don gian, danh dau chua trien khai day du.
        logger.warning("VNPay refund chua duoc trien khai day du")
        return RefundResult(
            success=False,
            message="VNPay refund chua duoc trien khai",
            refund_id=None,
        )

    async def get_status(self, transaction_id: str) -> dict[str, Any]:
        """Lay trang thai giao dich tu VNPay (queryDR)."""
        try:
            tmn_code = self._get_config_attr("vnp_TmnCode")
            secret = self._get_config_attr("vnp_HashSecret")
            api_url = self._get_config_attr("vnp_Api")

            if not api_url:
                return {"status": "unknown", "message": "vnp_Api chua duoc cau hinh"}

            now = datetime.now().strftime("%Y%m%d%H%M%S")
            params = {
                "vnp_Version": "2.1.0",
                "vnp_Command": "queryDR",
                "vnp_TmnCode": tmn_code,
                "vnp_TxnRef": transaction_id,
                "vnp_OrderInfo": f"Query {transaction_id}",
                "vnp_TransDate": now,  # Can actual trans date in production
                "vnp_CreateDate": now,
                "vnp_IpAddr": "127.0.0.1",
            }

            signature = self._generate_signature(params, secret)
            params["vnp_SecureHash"] = signature

            async with httpx.AsyncClient() as client:
                response = await client.post(api_url, data=params, timeout=30)
                response.raise_for_status()
                return {"status": "queried", "data": response.text}

        except Exception as e:
            logger.exception("VNPay get_status error: %s", e)
            return {"status": "error", "message": str(e)}
