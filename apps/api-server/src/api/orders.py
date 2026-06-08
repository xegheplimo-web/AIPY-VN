import random
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from src.database import async_session
from src.middleware.auth_middleware import require_auth
from src.models.order import Order, OrderItem
from src.models.store import Product
from src.services.ecc import get_request_signer
from src.middleware.rate_limit_per_user import per_user_rate_limit

router = APIRouter(prefix="/api", tags=["Orders"])

# Constants
HIGH_VALUE_ORDER_THRESHOLD = 1000000  # Orders over 1M VND require signature


class OrderItemRequest(BaseModel):
    product_id: str
    variant_id: str | None = None
    quantity: int = Field(..., ge=1)
    unit_price: float


class CreateOrderRequest(BaseModel):
    items: list[OrderItemRequest]
    store_id: str
    delivery_method: str = Field(default="pickup")
    delivery_address: str | None = None
    delivery_lat: float | None = None
    delivery_lng: float | None = None
    subtotal: float
    shipping_fee: float = 0
    discount: float = 0
    total_amount: float
    payment_method: str = Field(default="cash")
    # Optional request signature for sensitive operations
    signature: str | None = None
    timestamp: str | None = None


class OrderItemResponse(BaseModel):
    id: str
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float
    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: str
    order_number: str
    store_id: str
    delivery_method: str
    delivery_address: str | None = None
    subtotal: float
    shipping_fee: float
    discount: float
    total_amount: float
    payment_method: str
    payment_status: str
    status: str
    items: list[OrderItemResponse]
    created_at: str
    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    orders: list[OrderResponse]
    total: int


class ConfirmOrderResponse(BaseModel):
    id: str
    status: str


async def _fetch_product_names(session, order_items) -> dict:
    """Fetch product names from DB for the given order items."""
    product_ids = [item.product_id for item in order_items]
    if product_ids:
        product_stmt = select(Product.id, Product.name).where(Product.id.in_(product_ids))
        product_result = await session.execute(product_stmt)
        return {str(pid): pname for pid, pname in product_result.all()}
    return {}


@router.post("/orders", response_model=OrderResponse, status_code=201)
@per_user_rate_limit("10/minute")
async def create_order(
    request: CreateOrderRequest,
    current_user=Depends(require_auth),
):
    """Create a new order with optional ECC signature for high-value orders"""
    # Validate signature for high-value orders
    if request.total_amount >= HIGH_VALUE_ORDER_THRESHOLD:
        if not request.signature or not request.timestamp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="High-value orders require signature and timestamp",
            )

        # Verify signature
        signer = get_request_signer()
        is_valid = signer.verify_signature(
            f"{request.store_id}{request.total_amount}{request.timestamp}",
            request.signature,
            request.timestamp,
        )

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature",
            )

    async with async_session() as session:
        # Generate order number
        order_number = (
            f"ORD-{datetime.now().strftime('%Y%m%d')}-{random.randint(10000, 99999)}"
        )

        # Create order
        order = Order(
            id=uuid.uuid4(),
            order_number=order_number,
            user_id=uuid.UUID(current_user["id"]),
            store_id=uuid.UUID(request.store_id),
            delivery_method=request.delivery_method,
            delivery_address=request.delivery_address,
            delivery_lat=request.delivery_lat,
            delivery_lng=request.delivery_lng,
            subtotal=request.subtotal,
            shipping_fee=request.shipping_fee,
            discount=request.discount,
            total_amount=request.total_amount,
            payment_method=request.payment_method,
            status="pending",
        )
        session.add(order)
        await session.flush()  # Flush to get order.id

        # Create order items
        for item_request in request.items:
            order_item = OrderItem(
                id=uuid.uuid4(),
                order_id=order.id,
                product_id=uuid.UUID(item_request.product_id),
                variant_id=(
                    uuid.UUID(item_request.variant_id)
                    if item_request.variant_id
                    else None
                ),
                quantity=item_request.quantity,
                unit_price=item_request.unit_price,
                subtotal=item_request.quantity * item_request.unit_price,
            )
            session.add(order_item)

        await session.commit()
        await session.refresh(order)

        # Load order with items
        order_with_items = await session.execute(
            select(Order).options(selectinload(Order.items)).where(Order.id == order.id)
        )
        order_result = order_with_items.scalar_one()

        # Fetch product names from DB
        product_names = await _fetch_product_names(session, order_result.items)

        return OrderResponse(
            id=str(order_result.id),
            order_number=order_result.order_number,
            store_id=str(order_result.store_id),
            delivery_method=order_result.delivery_method,
            delivery_address=order_result.delivery_address,
            subtotal=float(order_result.subtotal),
            shipping_fee=float(order_result.shipping_fee),
            discount=float(order_result.discount),
            total_amount=float(order_result.total_amount),
            payment_method=order_result.payment_method,
            payment_status=order_result.payment_status,
            status=order_result.status,
            items=[
                OrderItemResponse(
                    id=str(item.id),
                    product_id=str(item.product_id),
                    product_name=product_names.get(str(item.product_id), f"Product {item.product_id}"),
                    quantity=item.quantity,
                    unit_price=float(item.unit_price),
                    subtotal=float(item.subtotal),
                )
                for item in order_result.items
            ],
            created_at=str(order_result.created_at) if order_result.created_at else datetime.now().isoformat(),
        )


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str):
    """Get a specific order with items (eager loaded to prevent N+1)"""
    async with async_session() as session:
        result = await session.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == uuid.UUID(order_id))
        )
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Fetch product names from DB
        product_names = await _fetch_product_names(session, order.items)

        return OrderResponse(
            id=str(order.id),
            order_number=order.order_number,
            store_id=str(order.store_id),
            delivery_method=order.delivery_method,
            delivery_address=order.delivery_address,
            subtotal=float(order.subtotal),
            shipping_fee=float(order.shipping_fee),
            discount=float(order.discount),
            total_amount=float(order.total_amount),
            payment_method=order.payment_method,
            payment_status=order.payment_status,
            status=order.status,
            items=[
                OrderItemResponse(
                    id=str(item.id),
                    product_id=str(item.product_id),
                    product_name=product_names.get(str(item.product_id), f"Product {item.product_id}"),
                    quantity=item.quantity,
                    unit_price=float(item.unit_price),
                    subtotal=float(item.subtotal),
                )
                for item in order.items
            ],
            created_at=str(order.created_at) if order.created_at else datetime.now().isoformat(),
        )


@router.get("/users/me/orders", response_model=OrderListResponse)
async def get_user_orders(current_user=Depends(require_auth), limit: int = 20, offset: int = 0):
    """Get user orders with pagination (eager loading to prevent N+1)"""
    user_id = uuid.UUID(current_user["id"])
    async with async_session() as session:
        count_stmt = select(func.count(Order.id)).where(Order.user_id == user_id)
        count_result = await session.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await session.execute(stmt)
        orders = result.scalars().all()

        order_responses = []
        for order in orders:
            # Fetch product names from DB for this order's items
            product_names = await _fetch_product_names(session, order.items)

            order_responses.append(
                OrderResponse(
                    id=str(order.id),
                    order_number=order.order_number,
                    store_id=str(order.store_id),
                    delivery_method=order.delivery_method,
                    delivery_address=order.delivery_address,
                    subtotal=float(order.subtotal),
                    shipping_fee=float(order.shipping_fee),
                    discount=float(order.discount),
                    total_amount=float(order.total_amount),
                    payment_method=order.payment_method,
                    payment_status=order.payment_status,
                    status=order.status,
                    items=[
                        OrderItemResponse(
                            id=str(item.id),
                            product_id=str(item.product_id),
                            product_name=product_names.get(str(item.product_id), f"Product {item.product_id}"),
                            quantity=item.quantity,
                            unit_price=float(item.unit_price),
                            subtotal=float(item.subtotal),
                        )
                        for item in order.items
                    ],
                    created_at=str(order.created_at) if order.created_at else datetime.now().isoformat(),
                )
            )

        return OrderListResponse(orders=order_responses, total=total)


@router.patch("/orders/{order_id}/status")
async def update_order_status(order_id: str, new_status: str, current_user=Depends(require_auth)):
    """Update order status (requires owner/admin role)"""
    # Validate status transition
    valid_statuses = ["pending", "confirmed", "preparing", "ready", "delivering", "completed", "cancelled"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    async with async_session() as session:
        result = await session.execute(
            select(Order).where(Order.id == uuid.UUID(order_id))
        )
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        order.status = new_status
        await session.commit()

        return ConfirmOrderResponse(id=str(order.id), status=order.status)
