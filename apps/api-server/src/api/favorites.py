"""
Favorites/Wishlist API for VietStore RAG.

Endpoints for managing user favorite products.
"""

from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from src.database import async_session
from src.middleware.auth_middleware import require_auth
from src.models.favorite import Favorite
from src.models.store import Product
from src.models.user import User

router = APIRouter(prefix="/api/favorites", tags=["Favorites"])


# ─── Pydantic Schemas ───────────────────────────────────────────────────────


class FavoriteItem(BaseModel):
    """A favorite item with product details."""

    id: str
    product_id: str
    name: str
    price: float
    image_url: Optional[str] = None
    store_name: str
    added_at: str

    class Config:
        from_attributes = True


class FavoriteListResponse(BaseModel):
    """Response for listing favorites."""

    items: List[FavoriteItem]
    total: int


class FavoriteToggleRequest(BaseModel):
    """Request to add/remove a favorite."""

    product_id: str = Field(
        ..., description="UUID of the product to favorite/unfavorite"
    )


class FavoriteToggleResponse(BaseModel):
    """Response after toggling a favorite."""

    product_id: str
    is_favorite: bool
    message: str


class FavoriteCheckResponse(BaseModel):
    """Response for checking if a product is favorited."""

    product_id: str
    is_favorite: bool


# ─── Helpers ──────────────────────────────────────────────────────────────────


async def _get_favorites_query(user_id: uuid.UUID):
    """Build query for fetching user's favorites with product details."""
    return (
        select(Favorite, Product)
        .join(Product, Favorite.product_id == Product.id)
        .where(Favorite.user_id == user_id)
        .order_by(Favorite.created_at.desc())
    )


# ─── Routes ───────────────────────────────────────────────────────────────────


@router.get("/", response_model=FavoriteListResponse)
async def list_favorites(current_user: User = Depends(require_auth)):
    """Get all favorite products for the current user."""
    async with async_session() as session:
        query = await _get_favorites_query(current_user.id)
        result = await session.execute(query)
        rows = result.all()

        items = []
        for fav, product in rows:
            # Get store name via relationship
            store_name = product.store.name if product.store else "Unknown"
            images = product.images or []
            image_url = images[0] if isinstance(images, list) and images else None
            if not image_url and isinstance(images, dict):
                image_url = images.get("thumbnail") or images.get("main")

            items.append(
                FavoriteItem(
                    id=str(fav.id),
                    product_id=str(product.id),
                    name=product.name,
                    price=float(product.price) if product.price else 0.0,
                    image_url=image_url,
                    store_name=store_name,
                    added_at=str(fav.created_at) if fav.created_at else None,
                )
            )

        return FavoriteListResponse(items=items, total=len(items))


@router.post("/toggle", response_model=FavoriteToggleResponse)
async def toggle_favorite(
    data: FavoriteToggleRequest,
    current_user: User = Depends(require_auth),
):
    """Add or remove a product from favorites (toggle behavior)."""
    try:
        product_uuid = uuid.UUID(data.product_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product_id format",
        )

    async with async_session() as session:
        # Check if product exists
        product_result = await session.execute(
            select(Product).where(Product.id == product_uuid)
        )
        product = product_result.scalar_one_or_none()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )

        # Check existing favorite
        existing_result = await session.execute(
            select(Favorite).where(
                Favorite.user_id == current_user.id,
                Favorite.product_id == product_uuid,
            )
        )
        existing = existing_result.scalar_one_or_none()

        if existing:
            # Remove from favorites
            await session.delete(existing)
            await session.commit()
            return FavoriteToggleResponse(
                product_id=data.product_id,
                is_favorite=False,
                message="Removed from favorites",
            )
        else:
            # Add to favorites
            favorite = Favorite(
                id=uuid.uuid4(),
                user_id=current_user.id,
                product_id=product_uuid,
            )
            session.add(favorite)
            await session.commit()
            return FavoriteToggleResponse(
                product_id=data.product_id,
                is_favorite=True,
                message="Added to favorites",
            )


@router.get("/check/{product_id}", response_model=FavoriteCheckResponse)
async def check_favorite(
    product_id: str,
    current_user: User = Depends(require_auth),
):
    """Check if a specific product is in the user's favorites."""
    try:
        product_uuid = uuid.UUID(product_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product_id format",
        )

    async with async_session() as session:
        result = await session.execute(
            select(Favorite).where(
                Favorite.user_id == current_user.id,
                Favorite.product_id == product_uuid,
            )
        )
        existing = result.scalar_one_or_none()

        return FavoriteCheckResponse(
            product_id=product_id,
            is_favorite=existing is not None,
        )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    product_id: str,
    current_user: User = Depends(require_auth),
):
    """Remove a product from favorites by product_id."""
    try:
        product_uuid = uuid.UUID(product_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product_id format",
        )

    async with async_session() as session:
        result = await session.execute(
            delete(Favorite).where(
                Favorite.user_id == current_user.id,
                Favorite.product_id == product_uuid,
            )
        )
        await session.commit()

        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Favorite not found",
            )
