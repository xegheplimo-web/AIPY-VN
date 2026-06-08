import uuid
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, update

from src.database import async_session
from src.models.store import Product
from src.models.order import Cart, CartItem

router = APIRouter(prefix="/api/cart", tags=["Cart"])


class CartProductInfo(BaseModel):
    id: str
    name: str
    price: float
    stock: int
    unit: str
    images: Optional[List[str]] = None
    model_config = {"from_attributes": True}


class CartItemResponse(BaseModel):
    id: str
    product: CartProductInfo
    quantity: int
    unit_price: float
    subtotal: float
    model_config = {"from_attributes": True}


class CartResponse(BaseModel):
    cart_id: str
    store_id: Optional[str] = None
    items: List[CartItemResponse]
    total_items: int
    total_amount: float


class AddCartItemRequest(BaseModel):
    product_id: str
    quantity: int = Field(default=1, ge=1)


class AddCartItemResponse(BaseModel):
    item_id: str
    status: str
    message: str


class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(..., ge=0)


class UpdateCartItemResponse(BaseModel):
    item_id: str
    quantity: int
    status: str


class RemoveCartItemResponse(BaseModel):
    item_id: str
    status: str
    message: str


@router.get("/", response_model=CartResponse)
async def get_cart(user_id: Optional[str] = None):
    async with async_session() as session:
        # For now, get the active cart (in real app, filter by user_id)
        cart_stmt = select(Cart).where(Cart.status == "active")
        if user_id:
            cart_stmt = cart_stmt.where(Cart.user_id == uuid.UUID(user_id))
        cart_stmt = cart_stmt.order_by(Cart.created_at.desc()).limit(1)

        cart_result = await session.execute(cart_stmt)
        cart = cart_result.scalar_one_or_none()

        if not cart:
            return CartResponse(
                cart_id="",
                items=[],
                total_items=0,
                total_amount=0.0,
            )

        # Get cart items with products
        items_stmt = (
            select(CartItem, Product)
            .join(Product, CartItem.product_id == Product.id)
            .where(CartItem.cart_id == cart.id)
        )
        items_result = await session.execute(items_stmt)
        rows = items_result.all()

        items = []
        total_amount = 0.0
        for cart_item, product in rows:
            subtotal = float(cart_item.unit_price) * cart_item.quantity
            total_amount += subtotal
            items.append(
                CartItemResponse(
                    id=str(cart_item.id),
                    product=CartProductInfo(
                        id=str(product.id),
                        name=product.name,
                        price=float(product.price) if product.price else 0.0,
                        stock=product.stock,
                        unit=product.unit or "cai",
                        images=product.images,
                    ),
                    quantity=cart_item.quantity,
                    unit_price=float(cart_item.unit_price),
                    subtotal=subtotal,
                )
            )

        return CartResponse(
            cart_id=str(cart.id),
            store_id=str(cart.store_id) if cart.store_id else None,
            items=items,
            total_items=len(items),
            total_amount=total_amount,
        )


@router.post("/items", response_model=AddCartItemResponse)
async def add_to_cart(data: AddCartItemRequest, user_id: Optional[str] = None):
    async with async_session() as session:
        # Get product
        product_stmt = select(Product).where(Product.id == uuid.UUID(data.product_id))
        product_result = await session.execute(product_stmt)
        product = product_result.scalar_one_or_none()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        if product.stock < data.quantity:
            raise HTTPException(status_code=400, detail="Not enough stock")

        # Get or create cart
        cart_stmt = select(Cart).where(Cart.status == "active")
        if user_id:
            cart_stmt = cart_stmt.where(Cart.user_id == uuid.UUID(user_id))
        cart_stmt = cart_stmt.order_by(Cart.created_at.desc()).limit(1)

        cart_result = await session.execute(cart_stmt)
        cart = cart_result.scalar_one_or_none()

        if not cart:
            cart = Cart(
                id=uuid.uuid4(),
                user_id=uuid.UUID(user_id) if user_id else None,
                store_id=product.store_id,
                status="active",
            )
            session.add(cart)
            await session.flush()

        # Check if item already in cart
        existing_stmt = select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == uuid.UUID(data.product_id),
        )
        existing_result = await session.execute(existing_stmt)
        existing = existing_result.scalar_one_or_none()

        if existing:
            # Use atomic update with row-level lock to prevent race conditions
            await session.execute(
                update(CartItem)
                .where(CartItem.id == existing.id)
                .values(
                    quantity=CartItem.quantity + data.quantity, unit_price=product.price
                )
                .with_for_update()  # Row-level lock
            )
            await session.commit()
            await session.refresh(existing)
            return AddCartItemResponse(
                item_id=str(existing.id),
                status="updated",
                message="Cart item quantity updated",
            )

        # Create new cart item
        cart_item = CartItem(
            id=uuid.uuid4(),
            cart_id=cart.id,
            product_id=uuid.UUID(data.product_id),
            quantity=data.quantity,
            unit_price=product.price,
        )
        session.add(cart_item)
        await session.commit()

        return AddCartItemResponse(
            item_id=str(cart_item.id),
            status="added",
            message="Item added to cart",
        )


@router.put("/items/{item_id}", response_model=UpdateCartItemResponse)
async def update_cart_item(item_id: str, data: UpdateCartItemRequest):
    async with async_session() as session:
        stmt = select(CartItem).where(CartItem.id == uuid.UUID(item_id))
        result = await session.execute(stmt)
        item = result.scalar_one_or_none()

        if not item:
            raise HTTPException(status_code=404, detail="Cart item not found")

        if data.quantity == 0:
            await session.delete(item)
            await session.commit()
            return UpdateCartItemResponse(
                item_id=item_id,
                quantity=0,
                status="removed",
            )

        item.quantity = data.quantity
        await session.commit()

        return UpdateCartItemResponse(
            item_id=item_id,
            quantity=data.quantity,
            status="updated",
        )


@router.delete("/items/{item_id}", response_model=RemoveCartItemResponse)
async def remove_from_cart(item_id: str):
    async with async_session() as session:
        stmt = select(CartItem).where(CartItem.id == uuid.UUID(item_id))
        result = await session.execute(stmt)
        item = result.scalar_one_or_none()

        if not item:
            raise HTTPException(status_code=404, detail="Cart item not found")

        await session.delete(item)
        await session.commit()

        return RemoveCartItemResponse(
            item_id=item_id,
            status="removed",
            message="Item removed from cart",
        )
