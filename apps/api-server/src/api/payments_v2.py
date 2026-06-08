"""
Payments API v2 - Multi-gateway payment processing

Ho tro nhieu cong thanh toan: Stripe, VNPay, MoMo, ZaloPay, COD.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.database import async_session
from src.middleware.auth_middleware import require_auth
from src.models.order import Order
from src.models.payment import PaymentTransaction
from src.models.user import User
from src.services.payment_factory import PaymentGatewayFactory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments-v2"])


# ---------------------------------------------------------------------------
# Schemas (Pydantic)
# ---------------------------------------------------------------------------


class CreatePaymentRequest(BaseModel):
    """Yeu cau tao thanh toan."""

    order_id: str = Field(..., description="Ma don hang")
    gateway: str = Field(
        ..., description="Cong thanh toan (stripe, vnpay, momo, zalopay, cod)"
    )
    amount: float = Field(..., gt=0, description="So tien thanh toan")
    currency: str = Field(default="VND", description="Ma tien te")
    description: str = Field(default="", description="Mo ta giao dich")
    return_url: str = Field(..., description="URL quay ve sau thanh toan")
    cancel_url: str = Field(default="", description="URL quay ve khi huy")
    metadata: dict[str, Any] | None = Field(default=None, description="Du lieu bo sung")


class CreatePaymentResponse(BaseModel):
    """Phan hoi tao thanh toan."""

    success: bool
    message: str
    transaction_id: str | None = None
    gateway_url: str | None = None
    raw_response: dict[str, Any] | None = None


class VerifyPaymentResponse(BaseModel):
    """Phan hoi xac minh thanh toan."""

    success: bool
    message: str
    transaction_id: str | None = None
    status: str | None = None


class WebhookResponse(BaseModel):
    """Phan hoi webhook."""

    success: bool
    message: str


class RefundRequest(BaseModel):
    """Yeu cau hoan tien."""

    transaction_id: str = Field(..., description="Ma giao dich can hoan tien")
    amount: float | None = Field(
        None, gt=0, description="So tien hoan (None = hoan toan bo)"
    )
    reason: str | None = Field(None, description="Ly do hoan tien")


class RefundResponse(BaseModel):
    """Phan hoi hoan tien."""

    success: bool
    message: str
    refund_id: str | None = None


class PaymentTransactionResponse(BaseModel):
    """Thong tin giao dich thanh toan."""

    id: str
    order_id: str | None
    gateway: str
    gateway_transaction_id: str | None
    amount: float
    currency: str
    status: str
    created_at: str | None
    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _to_uuid(val: str | uuid.UUID | None) -> uuid.UUID | None:
    """Chuyen doi chuoi sang UUID."""
    if val is None:
        return None
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/create", response_model=CreatePaymentResponse)
async def create_payment(
    request: CreatePaymentRequest,
    current_user: User = Depends(require_auth),
):
    """
    Tao yeu cau thanh toan moi.

    - Luu trang thai pending vao DB
    - Goi gateway.create_payment()
    - Tra ve gateway_url de redirect nguoi dung
    """
    try:
        gateway = PaymentGatewayFactory.get_gateway(request.gateway)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    order_uuid = _to_uuid(request.order_id)
    if not order_uuid:
        raise HTTPException(status_code=400, detail="order_id khong hop le")

    async with async_session() as session:
        # Kiem tra don hang ton tai
        order_result = await session.execute(
            select(Order).where(Order.id == order_uuid)
        )
        order = order_result.scalar_one_or_none()
        if not order:
            raise HTTPException(status_code=404, detail="Don hang khong ton tai")

        # Tao ban ghi PaymentTransaction
        tx = PaymentTransaction(
            order_id=order_uuid,
            user_id=_to_uuid(current_user.id) if hasattr(current_user, "id") else None,
            gateway=request.gateway.lower(),
            amount=request.amount,
            currency=request.currency.upper(),
            status="pending",
            request_data={
                "order_id": request.order_id,
                "amount": request.amount,
                "currency": request.currency,
                "description": request.description,
                "return_url": request.return_url,
                "cancel_url": request.cancel_url,
                "metadata": request.metadata,
            },
        )
        session.add(tx)
        await session.commit()
        await session.refresh(tx)

        # Goi gateway tao thanh toan
        result = await gateway.create_payment(
            order_id=request.order_id,
            amount=request.amount,
            currency=request.currency,
            description=request.description
            or f"Thanh toan don hang {request.order_id}",
            return_url=request.return_url,
            cancel_url=request.cancel_url or request.return_url,
            metadata=request.metadata,
        )

        # Cap nhat transaction voi ket qua
        tx.response_data = result.raw_response
        tx.gateway_transaction_id = result.transaction_id
        if result.success:
            tx.status = "processing"
        else:
            tx.status = "failed"
        await session.commit()

        return CreatePaymentResponse(
            success=result.success,
            message=result.message,
            transaction_id=str(tx.id),
            gateway_url=result.gateway_url,
            raw_response=result.raw_response,
        )


@router.get("/verify/{gateway}", response_model=VerifyPaymentResponse)
async def verify_payment(gateway: str, request: Request):
    """
    Xac minh ket qua thanh toan tu return URL cua cong thanh toan.

    - Gateway tra ve query params
    - Kiem tra chu ky va cap nhat trang thai DB
    """
    try:
        gw = PaymentGatewayFactory.get_gateway(gateway)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Lay query params tu request
    query_params = dict(request.query_params)

    result = await gw.verify_payment(query_params)

    # Cap nhat DB neu tim thay transaction
    txn_ref = result.transaction_id
    if txn_ref:
        async with async_session() as session:
            stmt = (
                select(PaymentTransaction)
                .where(PaymentTransaction.gateway_transaction_id == txn_ref)
                .where(PaymentTransaction.gateway == gateway.lower())
            )
            tx_result = await session.execute(stmt)
            tx = tx_result.scalar_one_or_none()
            if tx:
                tx.status = "success" if result.success else "failed"
                if tx.response_data:
                    tx.response_data.update(result.raw_response)
                else:
                    tx.response_data = result.raw_response
                await session.commit()

    return VerifyPaymentResponse(
        success=result.success,
        message=result.message,
        transaction_id=txn_ref,
        status="success" if result.success else "failed",
    )


@router.post("/webhook/{gateway}", response_model=WebhookResponse)
async def process_webhook(gateway: str, request: Request):
    """
    Xu ly webhook/IPN tu cong thanh toan.

    - Nhan payload tho tu gateway
    - Xac minh chu ky va cap nhat trang thai giao dich
    """
    try:
        gw = PaymentGatewayFactory.get_gateway(gateway)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    body = await request.body()
    headers = dict(request.headers)

    result = await gw.process_webhook(body, headers)

    # Cap nhat DB
    txn_ref = result.transaction_id
    if txn_ref:
        async with async_session() as session:
            stmt = (
                select(PaymentTransaction)
                .where(PaymentTransaction.gateway_transaction_id == txn_ref)
                .where(PaymentTransaction.gateway == gateway.lower())
            )
            tx_result = await session.execute(stmt)
            tx = tx_result.scalar_one_or_none()
            if tx:
                tx.status = "success" if result.success else "failed"
                tx.webhook_data = result.raw_response
                await session.commit()

    return WebhookResponse(success=result.success, message=result.message)


@router.post("/refund-request", response_model=RefundResponse)
async def refund_payment(
    request: RefundRequest,
    current_user: User = Depends(require_auth),
):
    """
    Hoan tien cho giao dich.

    - Tim transaction theo ID
    - Xac dinh gateway va goi refund
    - Cap nhat trang thai hoan tien
    """
    tx_uuid = _to_uuid(request.transaction_id)
    if not tx_uuid:
        raise HTTPException(status_code=400, detail="transaction_id khong hop le")

    async with async_session() as session:
        tx_result = await session.execute(
            select(PaymentTransaction).where(PaymentTransaction.id == tx_uuid)
        )
        tx = tx_result.scalar_one_or_none()
        if not tx:
            raise HTTPException(status_code=404, detail="Giao dich khong ton tai")

        try:
            gateway = PaymentGatewayFactory.get_gateway(tx.gateway)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        gw_txn_id = tx.gateway_transaction_id or str(tx.id)
        result = await gateway.refund(
            transaction_id=gw_txn_id,
            amount=request.amount,
            reason=request.reason,
        )

        if result.success:
            tx.status = "refunded"
            tx.refunded_amount = request.amount or tx.amount
            tx.refund_reason = request.reason
            await session.commit()

        return RefundResponse(
            success=result.success,
            message=result.message,
            refund_id=result.refund_id,
        )


@router.get("/transactions/{order_id}", response_model=list[PaymentTransactionResponse])
async def list_transactions(order_id: str):
    """
    Liet ke cac giao dich thanh toan cua mot don hang.
    """
    order_uuid = _to_uuid(order_id)
    if not order_uuid:
        raise HTTPException(status_code=400, detail="order_id khong hop le")

    async with async_session() as session:
        result = await session.execute(
            select(PaymentTransaction)
            .where(PaymentTransaction.order_id == order_uuid)
            .order_by(PaymentTransaction.created_at.desc())
        )
        transactions = result.scalars().all()

        return [
            PaymentTransactionResponse(
                id=str(tx.id),
                order_id=str(tx.order_id) if tx.order_id else None,
                gateway=tx.gateway,
                gateway_transaction_id=tx.gateway_transaction_id,
                amount=float(tx.amount),
                currency=tx.currency,
                status=tx.status,
                created_at=str(tx.created_at) if tx.created_at else None,
            )
            for tx in transactions
        ]
