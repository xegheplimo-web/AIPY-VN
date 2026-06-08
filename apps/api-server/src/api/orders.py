import random
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from src.database import async_session
from src.middleware.auth_middleware import require_auth
from src.models.order import Order, OrderItem
from src.models.store import Product
from src.services.ecc import get_request_signer

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
    confirmed_at: str


def generate_order_number():
    now = datetime.now()
    random_num = random.randint(1, 99999)
    return f"ORD-{now.strftime('%Y')}-{random_num:05d}"


async def verify_order_signature(
    data: CreateOrderRequest,
    signature: str | None,
    timestamp: str | None,
) -> bool:
    """
    Verify request signature for high-value orders.

    Args:
        data: Order request data
        signature: Request signature
        timestamp: Request timestamp

    Returns:
        True if signature is valid or not required, False otherwise
    """
    # Low-value orders don't require signature
    if data.total_amount <= HIGH_VALUE_ORDER_THRESHOLD:
        return True

    # High-value orders require signature
    if not signature or not timestamp:
        return False

    # Verify signature using ECDSA
    request_signer = get_request_signer()
    body = data.model_dump_json()
    is_valid = request_signer.verify_request(
        signature=signature,
        method="POST",
        path="/api/orders",
        body=body,
        timestamp=timestamp,
    )

    return is_valid


async def verify_product_stock(session, items: list[OrderItemRequest]) -> None:
    """
    Verify all products exist and have enough stock.

    Args:
        session: Database session
        items: List of order items

    Raises:
        HTTPException: If product not found or insufficient stock
    """
    for item in items:
        product_stmt = select(Product).where(Product.id == uuid.UUID(item.product_id))
        product_result = await session.execute(product_stmt)
        product = product_result.scalar_one_or_none()

        if not product:
            raise HTTPException(
                status_code=404, detail=f"Product {item.product_id} not found"
            )

        if product.stock < item.quantity:
            raise HTTPException(
                status_code=400, detail=f"Not enough stock for {product.name}"
            )


async def create_order_record(
    session,
    data: CreateOrderRequest,
    user_id: str,
) -> Order:
    """
    Create order record in database.

    Args:
        session: Database session
        data: Order request data
        user_id: User ID

    Returns:
        Created Order object
    """
    order = Order(
        id=uuid.uuid4(),
        order_number=generate_order_number(),
        user_id=uuid.UUID(user_id) if user_id else None,
        store_id=uuid.UUID(data.store_id),
        delivery_method=data.delivery_method,
        delivery_address=data.delivery_address,
        delivery_lat=data.delivery_lat,
        delivery_lng=data.delivery_lng,
        subtotal=data.subtotal,
        shipping_fee=data.shipping_fee,
        discount=data.discount,
        total_amount=data.total_amount,
        payment_method=data.payment_method,
        payment_status="pending",
        status="pending",
        created_at=datetime.now().isoformat(),
    )
    session.add(order)
    await session.flush()
    return order


async def create_order_items(
    session,
    order: Order,
    items: list[OrderItemRequest],
) -> list[OrderItem]:
    """
    Create order items and update product stock.

    Args:
        session: Database session
        order: Order object
        items: List of order items

    Returns:
        List of created OrderItem objects
    """
    order_items = []
    for item in items:
        product_stmt = select(Product).where(Product.id == uuid.UUID(item.product_id))
        product_result = await session.execute(product_stmt)
        product = product_result.scalar_one()

        # Decrease stock
        product.stock -= item.quantity

        order_item = OrderItem(
            id=uuid.uuid4(),
            order_id=order.id,
            product_id=uuid.UUID(item.product_id),
            variant_id=uuid.UUID(item.variant_id) if item.variant_id else None,
            quantity=item.quantity,
            unit_price=item.unit_price,
            subtotal=item.unit_price * item.quantity,
        )
        session.add(order_item)
        order_items.append(order_item)

    return order_items


@router.post("/orders", response_model=OrderResponse)
async def create_order(
    data: CreateOrderRequest,
    current_user: dict = Depends(require_auth),
    x_signature: str | None = Header(None, alias="X-Signature"),
    x_timestamp: str | None = Header(None, alias="X-Timestamp"),
):
    async with async_session() as session:
        # Get user_id from authenticated user
        user_id = current_user.get("id")

        # Verify signature
        signature = data.signature or x_signature
        timestamp = data.timestamp or x_timestamp
        if not await verify_order_signature(data, signature, timestamp):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing signature for high-value order",
            )

        # Verify product stock
        await verify_product_stock(session, data.items)

        # Create order record
        order = await create_order_record(session, data, user_id)

        # Create order items and update stock
        order_items = await create_order_items(session, order, data.items)

        await session.commit()

        # Build response
        items_response = []
        for oi in order_items:
            product_stmt = select(Product).where(Product.id == oi.product_id)
            product_result = await session.execute(product_stmt)
            product = product_result.scalar_one()

            items_response.append(
                OrderItemResponse(
                    id=str(oi.id),
                    product_id=str(oi.product_id),
                    product_name=product.name,
                    quantity=oi.quantity,
                    unit_price=float(oi.unit_price),
                    subtotal=float(oi.subtotal),
                )
            )

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
            items=items_response,
            created_at=order.created_at or datetime.now().isoformat(),
        )


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order_detail(order_id: str):
    async with async_session() as session:
        stmt = select(Order).where(Order.id == uuid.UUID(order_id))
        result = await session.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Get items with product names
        items_stmt = (
            select(OrderItem, Product.name)
            .join(Product, OrderItem.product_id == Product.id)
            .where(OrderItem.order_id == uuid.UUID(order_id))
        )
        items_result = await session.execute(items_stmt)
        rows = items_result.all()

        items = [
            OrderItemResponse(
                id=str(oi.id),
                product_id=str(oi.product_id),
                product_name=product_name,
                quantity=oi.quantity,
                unit_price=float(oi.unit_price),
                subtotal=float(oi.subtotal),
            )
            for oi, product_name in rows
        ]

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
            items=items,
            created_at=order.created_at or datetime.now().isoformat(),
        )


@router.get("/users/me/orders", response_model=OrderListResponse)
async def get_user_orders(user_id: str | None = None, limit: int = 20, offset: int = 0):
    async with async_session() as session:
        # In real app, get user_id from JWT token
        # For now, return all orders
        count_stmt = select(func.count(Order.id))
        if user_id:
            count_stmt = count_stmt.where(Order.user_id == uuid.UUID(user_id))
        count_result = await session.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = (
            select(Order).order_by(Order.created_at.desc()).limit(limit).offset(offset)
        )
        if user_id:
            stmt = stmt.where(Order.user_id == uuid.UUID(user_id))

        result = await session.execute(stmt)
        orders = result.scalars().all()

        order_responses = []
        for order in orders:
            items_stmt = (
                select(OrderItem, Product.name)
                .join(Product, OrderItem.product_id == Product.id)
                .where(OrderItem.order_id == order.id)
            )
            items_result = await session.execute(items_stmt)
            rows = items_result.all()

            items = [
                OrderItemResponse(
                    id=str(oi.id),
                    product_id=str(oi.product_id),
                    product_name=product_name,
                    quantity=oi.quantity,
                    unit_price=float(oi.unit_price),
                    subtotal=float(oi.subtotal),
                )
                for oi, product_name in rows
            ]

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
                    items=items,
                    created_at=order.created_at or "",
                )
            )

        return OrderListResponse(orders=order_responses, total=total)


@router.post("/orders/{order_id}/confirm", response_model=ConfirmOrderResponse)
async def confirm_order(order_id: str):
    async with async_session() as session:
        stmt = select(Order).where(Order.id == uuid.UUID(order_id))
        result = await session.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status != "pending":
            raise HTTPException(
                status_code=400,
                detail=f"Order cannot be confirmed (current status: {order.status})",
            )

        order.status = "confirmed"
        order.confirmed_at = datetime.now().isoformat()
        await session.commit()

        return ConfirmOrderResponse(
            id=order_id,
            status="confirmed",
            confirmed_at=order.confirmed_at,
        )
