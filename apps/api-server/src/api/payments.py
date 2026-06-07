"""
Payments API

Endpoints for payment processing using Stripe.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from src.services.stripe import get_stripe_service
from src.middleware.auth_middleware import require_auth
from src.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])


class CreatePaymentIntentRequest(BaseModel):
    """Request to create a payment intent."""

    amount: int = Field(..., gt=0, description="Amount in cents")
    currency: str = Field(default="usd", description="Currency code")
    order_id: Optional[str] = Field(None, description="Order ID")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")


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
    amount: Optional[int] = Field(None, description="Amount to refund in cents")


@router.post("/create-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    request: CreatePaymentIntentRequest,
    current_user: User = Depends(require_auth)
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
                message="Stripe not configured"
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
            metadata=metadata
        )
        
        if not result:
            return PaymentIntentResponse(
                success=False,
                message="Failed to create payment intent"
            )
        
        return PaymentIntentResponse(
            success=True,
            message="Payment intent created successfully",
            payment_intent_id=result["id"],
            client_secret=result["client_secret"],
            amount=result["amount"],
            currency=result["currency"]
        )
        
    except Exception as e:
        logger.error(f"Failed to create payment intent: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create payment intent: {str(e)}"
        )


@router.post("/confirm", response_model=PaymentIntentResponse)
async def confirm_payment(
    request: ConfirmPaymentRequest,
    current_user: User = Depends(require_auth)
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
                message="Stripe not configured"
            )
        
        # Confirm payment
        result = await stripe_service.confirm_payment(
            payment_intent_id=request.payment_intent_id,
            payment_method_id=request.payment_method_id
        )
        
        if not result:
            return PaymentIntentResponse(
                success=False,
                message="Failed to confirm payment"
            )
        
        return PaymentIntentResponse(
            success=True,
            message="Payment confirmed successfully",
            payment_intent_id=result["id"],
            amount=result["amount"]
        )
        
    except Exception as e:
        logger.error(f"Failed to confirm payment: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to confirm payment: {str(e)}"
        )


@router.get("/intent/{payment_intent_id}")
async def get_payment_intent(
    payment_intent_id: str,
    current_user: User = Depends(require_auth)
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
            detail=f"Failed to get payment intent: {str(e)}"
        )


@router.post("/refund")
async def refund_payment(
    request: RefundRequest,
    current_user: User = Depends(require_auth)
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
            amount=request.amount
        )
        
        if not result:
            return {"success": False, "message": "Failed to refund payment"}
        
        return {"success": True, "data": result}
        
    except Exception as e:
        logger.error(f"Failed to refund payment: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refund payment: {str(e)}"
        )


@router.post("/webhook")
async def stripe_webhook():
    """
    Handle Stripe webhooks.
    
    This endpoint processes webhook events from Stripe.
    """
    # TODO: Implement webhook signature verification
    # TODO: Handle different webhook events (payment_intent.succeeded, etc.)
    return {"success": True, "message": "Webhook received"}
