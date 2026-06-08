"""
Reviews API

Endpoints for managing store and product reviews.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from src.database import async_session
from src.models.user import User
from src.models.store import Store, Product
from src.middleware.auth_middleware import require_auth
from src.models.review import Review

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reviews", tags=["Reviews"])


class ReviewRequest(BaseModel):
    """Request to create or update a review."""

    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    comment: str = Field(..., min_length=1, max_length=1000, description="Review comment")
    store_id: Optional[str] = Field(None, description="Store ID (for store reviews)")
    product_id: Optional[str] = Field(None, description="Product ID (for product reviews)")


class ReviewResponse(BaseModel):
    """Response model for review."""

    id: str
    user_id: str
    user_name: Optional[str]
    store_id: Optional[str]
    product_id: Optional[str]
    rating: int
    comment: str
    created_at: str
    updated_at: Optional[str]
    model_config = {"from_attributes": True}


class ReviewListResponse(BaseModel):
    """Response model for review list."""

    reviews: List[ReviewResponse]
    total: int
    average_rating: Optional[float]


@router.post("", response_model=ReviewResponse, status_code=201)
async def create_review(
    data: ReviewRequest,
    current_user: User = Depends(require_auth),
):
    """
    Create a new review for a store or product.

    - User must be authenticated
    - Either store_id or product_id must be provided
    - User can only review once per store/product
    """
    if not data.store_id and not data.product_id:
        raise HTTPException(
            status_code=400, detail="Either store_id or product_id must be provided"
        )

    if data.store_id and data.product_id:
        raise HTTPException(
            status_code=400, detail="Cannot review both store and product at once"
        )

    async with async_session() as session:
        # Check if user already reviewed this store/product
        existing_query = select(Review).where(
            and_(
                Review.user_id == current_user.id,
                Review.store_id == data.store_id if data.store_id else None,
                Review.product_id == data.product_id if data.product_id else None,
            )
        )
        existing_result = await session.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=400, detail="You have already reviewed this item"
            )

        # Verify store/product exists
        if data.store_id:
            store_query = select(Store).where(Store.id == data.store_id)
            store_result = await session.execute(store_query)
            if not store_result.scalar_one_or_none():
                raise HTTPException(status_code=404, detail="Store not found")

        if data.product_id:
            product_query = select(Product).where(Product.id == data.product_id)
            product_result = await session.execute(product_query)
            if not product_result.scalar_one_or_none():
                raise HTTPException(status_code=404, detail="Product not found")

        # Create review
        review = Review(
            user_id=current_user.id,
            store_id=data.store_id,
            product_id=data.product_id,
            rating=data.rating,
            comment=data.comment,
        )

        session.add(review)
        await session.commit()
        await session.refresh(review)

        # Update store/product rating
        if data.store_id:
            await _update_store_rating(session, data.store_id)
        if data.product_id:
            await _update_product_rating(session, data.product_id)

        return ReviewResponse(
            id=str(review.id),
            user_id=str(review.user_id),
            user_name=current_user.full_name,
            store_id=str(review.store_id) if review.store_id else None,
            product_id=str(review.product_id) if review.product_id else None,
            rating=review.rating,
            comment=review.comment,
            created_at=review.created_at,
            updated_at=review.updated_at,
        )


@router.get("/stores/{store_id}", response_model=ReviewListResponse)
async def get_store_reviews(
    store_id: str,
    skip: int = 0,
    limit: int = 20,
):
    """
    Get all reviews for a specific store.

    - Returns paginated list of reviews
    - Includes average rating
    """
    async with async_session() as session:
        # Verify store exists
        store_query = select(Store).where(Store.id == store_id)
        store_result = await session.execute(store_query)
        store = store_result.scalar_one_or_none()
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")

        # Get reviews with user info
        reviews_query = (
            select(Review)
            .options(selectinload(Review.user))
            .where(Review.store_id == store_id)
            .order_by(Review.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        reviews_result = await session.execute(reviews_query)
        reviews = reviews_result.scalars().all()

        # Get total count
        count_query = select(Review).where(Review.store_id == store_id)
        count_result = await session.execute(count_query)
        total = count_result.scalar() or 0

        # Get average rating
        avg_query = select(Review.rating).where(Review.store_id == store_id)
        avg_result = await session.execute(avg_query)
        ratings = avg_result.scalars().all()
        average_rating = sum(ratings) / len(ratings) if ratings else None

        return ReviewListResponse(
            reviews=[
                ReviewResponse(
                    id=str(review.id),
                    user_id=str(review.user_id),
                    user_name=review.user.full_name if review.user else None,
                    store_id=str(review.store_id) if review.store_id else None,
                    product_id=str(review.product_id) if review.product_id else None,
                    rating=review.rating,
                    comment=review.comment,
                    created_at=review.created_at,
                    updated_at=review.updated_at,
                )
                for review in reviews
            ],
            total=total,
            average_rating=average_rating,
        )


@router.get("/products/{product_id}", response_model=ReviewListResponse)
async def get_product_reviews(
    product_id: str,
    skip: int = 0,
    limit: int = 20,
):
    """
    Get all reviews for a specific product.

    - Returns paginated list of reviews
    - Includes average rating
    """
    async with async_session() as session:
        # Verify product exists
        product_query = select(Product).where(Product.id == product_id)
        product_result = await session.execute(product_query)
        product = product_result.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Get reviews with user info
        reviews_query = (
            select(Review)
            .options(selectinload(Review.user))
            .where(Review.product_id == product_id)
            .order_by(Review.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        reviews_result = await session.execute(reviews_query)
        reviews = reviews_result.scalars().all()

        # Get total count
        count_query = select(Review).where(Review.product_id == product_id)
        count_result = await session.execute(count_query)
        total = count_result.scalar() or 0

        # Get average rating
        avg_query = select(Review.rating).where(Review.product_id == product_id)
        avg_result = await session.execute(avg_query)
        ratings = avg_result.scalars().all()
        average_rating = sum(ratings) / len(ratings) if ratings else None

        return ReviewListResponse(
            reviews=[
                ReviewResponse(
                    id=str(review.id),
                    user_id=str(review.user_id),
                    user_name=review.user.full_name if review.user else None,
                    store_id=str(review.store_id) if review.store_id else None,
                    product_id=str(review.product_id) if review.product_id else None,
                    rating=review.rating,
                    comment=review.comment,
                    created_at=review.created_at,
                    updated_at=review.updated_at,
                )
                for review in reviews
            ],
            total=total,
            average_rating=average_rating,
        )


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(review_id: str):
    """Get a specific review by ID."""
    async with async_session() as session:
        query = select(Review).options(selectinload(Review.user)).where(Review.id == review_id)
        result = await session.execute(query)
        review = result.scalar_one_or_none()

        if not review:
            raise HTTPException(status_code=404, detail="Review not found")

        return ReviewResponse(
            id=str(review.id),
            user_id=str(review.user_id),
            user_name=review.user.full_name if review.user else None,
            store_id=str(review.store_id) if review.store_id else None,
            product_id=str(review.product_id) if review.product_id else None,
            rating=review.rating,
            comment=review.comment,
            created_at=review.created_at,
            updated_at=review.updated_at,
        )


@router.put("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: str,
    data: ReviewRequest,
    current_user: User = Depends(require_auth),
):
    """
    Update an existing review.

    - User can only update their own reviews
    """
    async with async_session() as session:
        query = select(Review).where(Review.id == review_id)
        result = await session.execute(query)
        review = result.scalar_one_or_none()

        if not review:
            raise HTTPException(status_code=404, detail="Review not found")

        if review.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You can only update your own reviews")

        # Update review
        review.rating = data.rating
        review.comment = data.comment

        await session.commit()
        await session.refresh(review)

        # Update store/product rating
        if review.store_id:
            await _update_store_rating(session, review.store_id)
        if review.product_id:
            await _update_product_rating(session, review.product_id)

        return ReviewResponse(
            id=str(review.id),
            user_id=str(review.user_id),
            user_name=current_user.full_name,
            store_id=str(review.store_id) if review.store_id else None,
            product_id=str(review.product_id) if review.product_id else None,
            rating=review.rating,
            comment=review.comment,
            created_at=review.created_at,
            updated_at=review.updated_at,
        )


@router.delete("/{review_id}")
async def delete_review(
    review_id: str,
    current_user: User = Depends(require_auth),
):
    """
    Delete a review.

    - User can only delete their own reviews
    - Admin can delete any review
    """
    async with async_session() as session:
        query = select(Review).where(Review.id == review_id)
        result = await session.execute(query)
        review = result.scalar_one_or_none()

        if not review:
            raise HTTPException(status_code=404, detail="Review not found")

        if review.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="You can only delete your own reviews")

        store_id = review.store_id
        product_id = review.product_id

        await session.delete(review)
        await session.commit()

        # Update store/product rating
        if store_id:
            await _update_store_rating(session, store_id)
        if product_id:
            await _update_product_rating(session, product_id)

        return {"message": "Review deleted successfully"}


async def _update_store_rating(session, store_id: str):
    """Update store's average rating and total reviews."""
    from sqlalchemy import func

    query = select(
        func.avg(Review.rating).label("avg_rating"),
        func.count(Review.id).label("total_reviews"),
    ).where(Review.store_id == store_id)
    result = await session.execute(query)
    stats = result.first()

    store_query = select(Store).where(Store.id == store_id)
    store_result = await session.execute(store_query)
    store = store_result.scalar_one_or_none()

    if store:
        store.rating = float(stats.avg_rating) if stats.avg_rating else 0.0
        store.total_reviews = stats.total_reviews or 0
        await session.commit()


async def _update_product_rating(session, product_id: str):
    """Update product's average rating and total reviews."""
    from sqlalchemy import func

    query = select(
        func.avg(Review.rating).label("avg_rating"),
        func.count(Review.id).label("total_reviews"),
    ).where(Review.product_id == product_id)
    result = await session.execute(query)
    stats = result.first()

    product_query = select(Product).where(Product.id == product_id)
    product_result = await session.execute(product_query)
    product = product_result.scalar_one_or_none()

    if product:
        product.rating = float(stats.avg_rating) if stats.avg_rating else 0.0
        product.total_reviews = stats.total_reviews or 0
        await session.commit()
