"""
Payments API

Endpoints for payment processing using Stripe, including
authenticated webhook handling with signature verification.
"""

import logging

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from src.middleware.auth_middleware import require_auth
from src.models.user import User
from src.services.stripe import get_stripe_service
from src.services.payment_gateway import payment_gateway_service
from src.config import config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])


class CreatePaymentIntentRequest(BaseModel):
    """Request to create a payment intent."""

    amount: int = Field(..., gt=0, description="Amount in cents")
    currency: str = Field(default="usd", description="Currency code")
    order_id: str | None = Field(None, description="Order ID")
    metadata: dict | None = Field(default=None, description="Additional metadata")


class PaymentIntentResponse(BaseModel):
    """Response from payment intent creation."""

    success: bool
    message: str
    payment_intent_id: str = None
    client_secret: str = None
    amount: int = None
    currency: str = None


class ConfirmPaymentRequest(BaseModel):
    """Request to confirm a payment."""

    payment_intent_id: str = Field(..., description="Payment intent ID")
    payment_method_id: str = Field(..., description="Payment method ID")


class RefundRequest(BaseModel):
    """Request to refund a payment."""

    payment_intent_id: str = Field(..., description="Payment intent ID")
    amount: int | None = Field(None, description="Amount to refund in cents")


@router.post("/create-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    request: CreatePaymentIntentRequest,
    current_user: User = Depends(require_auth),
):
    """
    Create a Stripe payment intent.

    This endpoint creates a payment intent for processing payments.
    """
    try:
        stripe_service = get_stripe_service()

        if not stripe_service.is_ready():
            return PaymentIntentResponse(
                success=False,
                message="Stripe not configured",
            )

        # Build metadata
        metadata = request.metadata or {}
        if request.order_id:
            metadata["order_id"] = request.order_id
        metadata["user_id"] = str(current_user.id)

        # Create payment intent
        result = await stripe_service.create_payment_intent(
            amount=request.amount,
            currency=request.currency,
            metadata=metadata,
        )

        if not result:
            return PaymentIntentResponse(
                success=False,
                message="Failed to create payment intent",
            )

        return PaymentIntentResponse(
            success=True,
            message="Payment intent created successfully",
            payment_intent_id=result["id"],
            client_secret=result["client_secret"],
            amount=result["amount"],
            currency=result["currency"],
        )

    except Exception as e:
        logger.error(f"Failed to create payment intent: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create payment intent: {e!s}",
        )


@router.post("/confirm", response_model=PaymentIntentResponse)
async def confirm_payment(
    request: ConfirmPaymentRequest,
    current_user: User = Depends(require_auth),
):
    """
    Confirm a payment.

    This endpoint confirms a payment using a payment method.
    """
    try:
        stripe_service = get_stripe_service()

        if not stripe_service.is_ready():
            return PaymentIntentResponse(
                success=False,
                message="Stripe not configured",
            )

        # Confirm payment
        result = await stripe_service.confirm_payment(
            payment_intent_id=request.payment_intent_id,
            payment_method_id=request.payment_method_id,
        )

        if not result:
            return PaymentIntentResponse(
                success=False,
                message="Failed to confirm payment",
            )

        return PaymentIntentResponse(
            success=True,
            message="Payment confirmed successfully",
            payment_intent_id=result["id"],
            amount=result["amount"],
        )

    except Exception as e:
        logger.error(f"Failed to confirm payment: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to confirm payment: {e!s}",
        )


@router.get("/intent/{payment_intent_id}")
async def get_payment_intent(
    payment_intent_id: str,
    current_user: User = Depends(require_auth),
):
    """
    Get payment intent details.

    This endpoint retrieves the status and details of a payment intent.
    """
    try:
        stripe_service = get_stripe_service()

        if not stripe_service.is_ready():
            return {"success": False, "message": "Stripe not configured"}

        result = await stripe_service.get_payment_intent(payment_intent_id)

        if not result:
            return {"success": False, "message": "Failed to get payment intent"}

        return {"success": True, "data": result}

    except Exception as e:
        logger.error(f"Failed to get payment intent: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get payment intent: {e!s}",
        )


@router.post("/refund")
async def refund_payment(
    request: RefundRequest,
    current_user: User = Depends(require_auth),
):
    """
    Refund a payment.

    This endpoint creates a refund for a payment.
    """
    try:
        stripe_service = get_stripe_service()

        if not stripe_service.is_ready():
            return {"success": False, "message": "Stripe not configured"}

        # Create refund
        result = await stripe_service.refund_payment(
            payment_intent_id=request.payment_intent_id,
            amount=request.amount,
        )

        if not result:
            return {"success": False, "message": "Failed to refund payment"}

        return {"success": True, "data": result}

    except Exception as e:
        logger.error(f"Failed to refund payment: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refund payment: {e!s}",
        )


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhooks with signature verification.

    This endpoint processes webhook events from Stripe. It verifies
    the webhook signature using the Stripe signing secret to ensure
    the payload is authentic before processing.

    Supported events:
        - payment_intent.succeeded
        - payment_intent.payment_failed
        - charge.refunded
    """
    # Read the raw body – needed for signature verification
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature", "")

    webhook_secret = config.stripe.webhook_secret

    if not webhook_secret:
        logger.error(
            "Stripe webhook secret (STRIPE_WEBHOOK_SECRET) is not configured. "
            "Cannot verify webhook signature."
        )
        raise HTTPException(
            status_code=500,
            detail="Webhook endpoint not configured – missing signing secret",
        )

    # ------------------------------------------------------------------
    # Verify the webhook signature using Stripe's official helper
    # ------------------------------------------------------------------
    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            webhook_secret,
        )
    except ValueError as exc:
        # Invalid payload
        logger.warning(f"Stripe webhook – invalid payload: {exc}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as exc:
        # Invalid signature
        logger.warning(f"Stripe webhook – invalid signature: {exc}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as exc:
        logger.error(f"Stripe webhook – unexpected verification error: {exc}")
        raise HTTPException(status_code=400, detail="Webhook verification failed")

    # ------------------------------------------------------------------
    # Dispatch the verified event to the payment gateway service
    # ------------------------------------------------------------------
    event_type = event.get("type", "unknown")
    event_data = event.get("data", {})

    logger.info(
        f"Stripe webhook verified – event: {event_type}, id: {event.get('id', 'n/a')}"
    )

    try:
        await payment_gateway_service.handle_webhook_event(event_type, event_data)
    except Exception as exc:
        logger.error(f"Error handling webhook event {event_type}: {exc}")
        # Return 200 so Stripe doesn't keep retrying, but log the error
        return {"success": True, "message": "Webhook received (handler error logged)"}

    return {"success": True, "message": "Webhook received and processed"}
