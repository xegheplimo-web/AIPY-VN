"""
Categories API

Endpoints for managing product categories.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, select
from src.database import async_session
from src.middleware.auth_middleware import require_admin
from src.models.store import Category
from src.models.user import User
from src.utils.pagination import paginate, get_pagination_metadata

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/categories", tags=["Categories"])


class CategoryRequest(BaseModel):
    """Request to create or update a category."""

    name: str = Field(..., min_length=1, max_length=100)
    slug: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=500)
    icon: str | None = None
    is_active: bool = True


class CategoryResponse(BaseModel):
    """Response model for category."""

    id: str
    name: str
    slug: str | None
    description: str | None
    icon: str | None
    is_active: bool
    created_at: str
    updated_at: str | None
    model_config = {"from_attributes": True}


class CategoryListResponse(BaseModel):
    """Response model for category list with pagination."""

    categories: list[CategoryResponse]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool


@router.get("", response_model=CategoryListResponse)
async def get_categories(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    active_only: bool = True,
):
    """
    Get all categories with pagination.

    - Returns paginated list of categories
    - Can filter by active status
    """
    async with async_session() as session:
        query = select(Category)

        if active_only:
            query = query.where(Category.is_active)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination
        query = query.order_by(Category.name)
        query = paginate(query, page=page, limit=limit)
        result = await session.execute(query)
        categories = result.scalars().all()

        # Get pagination metadata
        metadata = get_pagination_metadata(total, page, limit)

        return CategoryListResponse(
            categories=[
                CategoryResponse(
                    id=str(cat.id),
                    name=cat.name,
                    slug=cat.slug,
                    description=cat.description,
                    icon=cat.icon,
                    is_active=cat.is_active,
                    created_at=cat.created_at,
                    updated_at=cat.updated_at,
                )
                for cat in categories
            ],
            total=total,
            page=page,
            limit=limit,
            total_pages=metadata["total_pages"],
            has_next=metadata["has_next"],
            has_prev=metadata["has_prev"],
        )


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: str):
    """Get a specific category by ID."""
    async with async_session() as session:
        query = select(Category).where(Category.id == category_id)
        result = await session.execute(query)
        category = result.scalar_one_or_none()

        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        return CategoryResponse(
            id=str(category.id),
            name=category.name,
            slug=category.slug,
            description=category.description,
            icon=category.icon,
            is_active=category.is_active,
            created_at=category.created_at,
            updated_at=category.updated_at,
        )


@router.post("", response_model=CategoryResponse, status_code=201)
async def create_category(
    data: CategoryRequest,
    current_user: User = Depends(require_admin),
):
    """
    Create a new category.

    - Only admin users can create categories
    - Slug will be auto-generated if not provided
    """
    async with async_session() as session:
        # Check if category with same name exists
        existing_query = select(Category).where(Category.name == data.name)
        existing_result = await session.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=400, detail="Category with this name already exists"
            )

        # Generate slug if not provided
        if not data.slug:
            slug = data.name.lower().replace(" ", "-").replace("/", "-")
        else:
            slug = data.slug

        # Check if slug already exists
        slug_query = select(Category).where(Category.slug == slug)
        slug_result = await session.execute(slug_query)
        if slug_result.scalar_one_or_none():
            raise HTTPException(
                status_code=400, detail="Category with this slug already exists"
            )

        # Create category
        category = Category(
            name=data.name,
            slug=slug,
            description=data.description,
            icon=data.icon,
            is_active=data.is_active,
        )

        session.add(category)
        await session.commit()
        await session.refresh(category)

        return CategoryResponse(
            id=str(category.id),
            name=category.name,
            slug=category.slug,
            description=category.description,
            icon=category.icon,
            is_active=category.is_active,
            created_at=category.created_at,
            updated_at=category.updated_at,
        )


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: str,
    data: CategoryRequest,
    current_user: User = Depends(require_admin),
):
    """
    Update an existing category.

    - Only admin users can update categories
    """
    async with async_session() as session:
        query = select(Category).where(Category.id == category_id)
        result = await session.execute(query)
        category = result.scalar_one_or_none()

        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        # Check if name is being changed and if new name already exists
        if data.name != category.name:
            existing_query = select(Category).where(
                and_(Category.name == data.name, Category.id != category_id)
            )
            existing_result = await session.execute(existing_query)
            if existing_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=400, detail="Category with this name already exists"
                )

        # Update category
        category.name = data.name
        category.description = data.description
        category.icon = data.icon
        category.is_active = data.is_active

        # Update slug if provided
        if data.slug:
            category.slug = data.slug
        else:
            # Auto-generate slug from name
            category.slug = data.name.lower().replace(" ", "-").replace("/", "-")

        await session.commit()
        await session.refresh(category)

        return CategoryResponse(
            id=str(category.id),
            name=category.name,
            slug=category.slug,
            description=category.description,
            icon=category.icon,
            is_active=category.is_active,
            created_at=category.created_at,
            updated_at=category.updated_at,
        )


@router.delete("/{category_id}")
async def delete_category(
    category_id: str,
    current_user: User = Depends(require_admin),
):
    """
    Delete a category.

    - Only admin users can delete categories
    - Cannot delete category if it has products
    """
    async with async_session() as session:
        query = select(Category).where(Category.id == category_id)
        result = await session.execute(query)
        category = result.scalar_one_or_none()

        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        # TODO: Check if category has products
        # For now, allow deletion

        await session.delete(category)
        await session.commit()

        return {"message": "Category deleted successfully"}
