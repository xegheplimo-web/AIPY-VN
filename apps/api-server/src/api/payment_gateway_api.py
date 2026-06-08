"""
Payment gateway API endpoints
"""

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Depends
from typing import Optional
from pydantic import BaseModel, Field
from src.middleware.auth_middleware import require_auth
from src.models.user import User
from src.services.payment_gateway import payment_gateway_service

router = APIRouter(prefix="/api/payments", tags=["Payments"])


class CreatePaymentIntentRequest(BaseModel):
    """Request model for creating payment intent"""

    amount: float = Field(..., gt=0, description="Amount in VND")
    currency: str = Field(default="vnd", description="Currency code")
    order_id: str = Field(..., description="Order ID")
    customer_email: Optional[str] = None
    metadata: Optional[dict] = None


class ConfirmPaymentIntentRequest(BaseModel):
    """Request model for confirming payment intent"""

    payment_intent_id: str
    payment_method_id: str


class CreateRefundRequest(BaseModel):
    """Request model for creating refund"""

    payment_intent_id: str
    amount: Optional[float] = None
    reason: Optional[str] = None


class CreateCustomerRequest(BaseModel):
    """Request model for creating customer"""

    email: str
    name: Optional[str] = None
    phone: Optional[str] = None
    metadata: Optional[dict] = None


@router.post("/create-intent")
async def create_payment_intent(
    request: CreatePaymentIntentRequest,
    current_user: User = Depends(require_auth),
):
    """
    Create a payment intent

    - Creates Stripe payment intent
    - Returns client secret for frontend
    - Includes order metadata
    """
    try:
        intent = await payment_gateway_service.create_payment_intent(
            amount=request.amount,
            currency=request.currency,
            order_id=request.order_id,
            customer_email=request.customer_email,
            metadata=request.metadata,
        )

        return intent

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confirm-intent")
async def confirm_payment_intent(
    request: ConfirmPaymentIntentRequest,
    current_user: User = Depends(require_auth),
):
    """
    Confirm a payment intent

    - Confirms Stripe payment intent
    - Processes payment
    - Returns payment status
    """
    try:
        intent = await payment_gateway_service.confirm_payment_intent(
            payment_intent_id=request.payment_intent_id,
            payment_method_id=request.payment_method_id,
        )

        return intent

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intent/{payment_intent_id}")
async def get_payment_intent(
    payment_intent_id: str,
    current_user: User = Depends(require_auth),
):
    """
    Retrieve payment intent status

    - Gets payment intent from Stripe
    - Returns current status
    - Includes metadata
    """
    try:
        intent = await payment_gateway_service.retrieve_payment_intent(
            payment_intent_id
        )

        return intent

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refund")
async def create_refund(
    request: CreateRefundRequest,
    current_user: User = Depends(require_auth),
):
    """
    Create a refund

    - Refunds payment intent
    - Supports partial refunds
    - Requires admin role
    """
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        refund = await payment_gateway_service.create_refund(
            payment_intent_id=request.payment_intent_id,
            amount=request.amount,
            reason=request.reason,
        )

        return refund

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/customer")
async def create_customer(
    request: CreateCustomerRequest,
    current_user: User = Depends(require_auth),
):
    """
    Create a Stripe customer

    - Creates customer in Stripe
    - Links to user account
    - Stores customer ID
    """
    try:
        customer = await payment_gateway_service.create_customer(
            email=request.email,
            name=request.name,
            phone=request.phone,
            metadata=request.metadata,
        )

        return customer

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def handle_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Handle Stripe webhook events

    - Verifies webhook signature
    - Processes payment events
    - Updates order status
    - Triggers notifications
    """
    # Get webhook signature
    sig_header = request.headers.get("stripe-signature")

    # Read payload
    payload = await request.body()

    # Verify signature
    is_valid = await payment_gateway_service.verify_webhook_signature(
        payload, sig_header
    )

    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Parse event
    import json

    event_data = json.loads(payload)
    event_type = event_data.get("type")

    # Handle event in background
    background_tasks.add_task(
        payment_gateway_service.handle_webhook_event(event_type, event_data)
    )

    return {"status": "received"}
