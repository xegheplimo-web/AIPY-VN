"""
Abstract base class and data classes for payment gateway integrations.

Cung cap lop co so truu tuong va cac dataclass cho cac cong thanh toan.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PaymentResult:
    """Ket qua tao thanh toan."""

    success: bool
    message: str = ""
    transaction_id: str | None = None
    gateway_url: str | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)


@dataclass
class RefundResult:
    """Ket qua hoan tien."""

    success: bool
    message: str = ""
    refund_id: str | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)


class PaymentGateway(ABC):
    """
    Lop co so truu tuong cho cac cong thanh toan.

    Moi cong thanh toan (Stripe, VNPay, MoMo, ZaloPay, COD)
    can ke thua va trien khai cac phuong thuc nay.
    """

    @abstractmethod
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
        """
        Tao yeu cau thanh toan moi.

        Args:
            order_id: Ma don hang
            amount: So tien thanh toan
            currency: Ma tien te (VND, USD, ...)
            description: Mo ta giao dich
            return_url: URL quay ve sau thanh toan thanh cong
            cancel_url: URL quay ve khi huy thanh toan
            metadata: Du lieu bo sung tuy chon

        Returns:
            PaymentResult voi gateway_url de redirect nguoi dung
        """
        ...

    @abstractmethod
    async def verify_payment(self, query_params: dict[str, Any]) -> PaymentResult:
        """
        Xac minh ket qua tra ve tu cong thanh toan (return URL).

        Args:
            query_params: Cac tham so query tu URL tra ve

        Returns:
            PaymentResult voi trang thai xac minh
        """
        ...

    @abstractmethod
    async def process_webhook(
        self, payload: bytes | str, headers: dict[str, Any]
    ) -> PaymentResult:
        """
        Xu ly thong bao webhook/IPN tu cong thanh toan.

        Args:
            payload: Du lieu tho cua webhook
            headers: Cac header kem theo

        Returns:
            PaymentResult voi trang thai cap nhat
        """
        ...

    @abstractmethod
    async def refund(
        self,
        transaction_id: str,
        amount: float | None = None,
        reason: str | None = None,
    ) -> RefundResult:
        """
        Hoan tien cho giao dich.

        Args:
            transaction_id: Ma giao dich can hoan tien
            amount: So tien hoan (None = hoan toan bo)
            reason: Ly do hoan tien

        Returns:
            RefundResult voi ket qua hoan tien
        """
        ...

    @abstractmethod
    async def get_status(self, transaction_id: str) -> dict[str, Any]:
        """
        Lay trang thai giao dich tu cong thanh toan.

        Args:
            transaction_id: Ma giao dich

        Returns:
            Dict chua thong tin trang thai
        """
        ...
