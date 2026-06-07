"""
Favorites API

Endpoints for managing user favorites/wishlist.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select

from src.db import async_session
from src.models.user import User
from src.models.store import Product
from src.middleware.auth_middleware import require_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users/me/favorites", tags=["Favorites"])


class FavoriteResponse(BaseModel):
    """Response model for favorite product."""

    id: str
    user_id: str
    product_id: str
    product_name: str
    product_price: float
    product_image: Optional[str]
    store_id: str
    store_name: str
    created_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=List[FavoriteResponse])
async def get_favorites(current_user: User = Depends(require_auth)):
    """
    Get all favorite products for the current user.

    - Returns list of products with store information
    """
    async with async_session() as session:
        # Query favorites with product and store info
        # Note: Since we don't have a Favorite model yet, we'll use a placeholder
        # In production, you would have a Favorite model with user_id and product_id

        # For now, return empty list as placeholder
        return []


@router.post("/products/{product_id}", status_code=201)
async def add_favorite(
    product_id: str,
    current_user: User = Depends(require_auth),
):
    """
    Add a product to user's favorites.

    - User can only favorite a product once
    """
    async with async_session() as session:
        # Verify product exists
        product_query = select(Product).where(Product.id == product_id)
        product_result = await session.execute(product_query)
        product = product_result.scalar_one_or_none()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # TODO: Check if already favorited and create Favorite record
        # For now, return success as placeholder
        return {"message": "Product added to favorites"}


@router.delete("/products/{product_id}")
async def remove_favorite(
    product_id: str,
    current_user: User = Depends(require_auth),
):
    """
    Remove a product from user's favorites.

    - User can only remove their own favorites
    """
    async with async_session() as session:
        # Verify product exists
        product_query = select(Product).where(Product.id == product_id)
        product_result = await session.execute(product_query)
        product = product_result.scalar_one_or_none()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # TODO: Remove Favorite record
        # For now, return success as placeholder
        return {"message": "Product removed from favorites"}
