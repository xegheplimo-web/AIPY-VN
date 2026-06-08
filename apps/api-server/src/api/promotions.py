"""
Promotions API for owner and admin
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, or_, select
from sqlalchemy.dialects.postgresql import UUID
from src.database import async_session
from src.middleware.auth_middleware import get_current_user, require_auth
from src.models.promotion import Promotion
from src.models.user import User
from src.utils.pagination import paginate, get_pagination_metadata

router = APIRouter(prefix="/api/v1/promotions", tags=["Promotions"])


class PromotionCreate(BaseModel):
    code: str = Field(..., min_length=3, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    type: str = Field(..., pattern="^(percentage|fixed|free_shipping)$")
    value: float | None = None
    min_order_amount: float = 0
    max_discount: float | None = None
    usage_limit: int | None = None
    start_date: str
    end_date: str
    applicable_stores: list[str] = Field(default_factory=lambda: ["all"])


class PromotionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    value: float | None = None
    min_order_amount: float | None = None
    max_discount: float | None = None
    usage_limit: int | None = None
    start_date: str | None = None
    end_date: str | None = None
    applicable_stores: list[str] | None = None
    status: str | None = None


class PromotionResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str | None
    type: str
    value: float | None
    min_order_amount: float
    max_discount: float | None
    usage_limit: int | None
    used_count: int
    start_date: str
    end_date: str
    status: str
    applicable_stores: list[str]
    created_at: str

    class Config:
        from_attributes = True


class PromotionListResponse(BaseModel):
    """Response model for promotion list with pagination."""

    promotions: list[PromotionResponse]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool


@router.get("", response_model=PromotionListResponse)
async def list_promotions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = None,
    search: str | None = None,
    current_user: User = Depends(get_current_user),
):
    """List all promotions with pagination (owner/admin only)"""
    if current_user.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    async with async_session() as session:
        query = select(Promotion)

        if status:
            query = query.where(Promotion.status == status)

        if search:
            query = query.where(
                or_(
                    Promotion.code.ilike(f"%{search}%"),
                    Promotion.name.ilike(f"%{search}%"),
                )
            )

        # Owners can only see their own promotions
        if current_user.role == "owner":
            # TODO: Filter by owner's store IDs
            pass

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination
        query = query.order_by(Promotion.created_at.desc())
        query = paginate(query, page=page, limit=limit)
        result = await session.execute(query)
        promotions = result.scalars().all()

        # Get pagination metadata
        metadata = get_pagination_metadata(total, page, limit)

        return PromotionListResponse(
            promotions=[
                PromotionResponse(
                    id=str(p.id),
                    code=p.code,
                    name=p.name,
                    description=p.description,
                    type=p.type,
                    value=float(p.value) if p.value else None,
                    min_order_amount=float(p.min_order_amount),
                    max_discount=float(p.max_discount) if p.max_discount else None,
                    usage_limit=p.usage_limit,
                    used_count=p.used_count,
                    start_date=p.start_date,
                    end_date=p.end_date,
                    status=p.status,
                    applicable_stores=p.applicable_stores or [],
                    created_at=str(p.created_at) if p.created_at else None,
                )
                for p in promotions
            ],
            total=total,
            page=page,
            limit=limit,
            total_pages=metadata["total_pages"],
            has_next=metadata["has_next"],
            has_prev=metadata["has_prev"],
        )


@router.post("", response_model=PromotionResponse, status_code=201)
async def create_promotion(
    promotion: PromotionCreate,
    current_user: User = Depends(require_auth),
):
    """Create a new promotion (owner/admin only)"""
    if current_user.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    async with async_session() as session:
        # Check if code already exists
        existing = await session.execute(
            select(Promotion).where(Promotion.code == promotion.code)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Promotion code already exists")

        new_promotion = Promotion(
            id=uuid.uuid4(),
            code=promotion.code.upper(),
            name=promotion.name,
            description=promotion.description,
            type=promotion.type,
            value=promotion.value,
            min_order_amount=promotion.min_order_amount,
            max_discount=promotion.max_discount,
            usage_limit=promotion.usage_limit,
            start_date=promotion.start_date,
            end_date=promotion.end_date,
            applicable_stores=promotion.applicable_stores,
            created_by=current_user.id,
            status="active",
        )

        session.add(new_promotion)
        await session.commit()
        await session.refresh(new_promotion)

        return PromotionResponse(
            id=str(new_promotion.id),
            code=new_promotion.code,
            name=new_promotion.name,
            description=new_promotion.description,
            type=new_promotion.type,
            value=float(new_promotion.value) if new_promotion.value else None,
            min_order_amount=float(new_promotion.min_order_amount),
            max_discount=(
                float(new_promotion.max_discount)
                if new_promotion.max_discount
                else None
            ),
            usage_limit=new_promotion.usage_limit,
            used_count=new_promotion.used_count,
            start_date=new_promotion.start_date,
            end_date=new_promotion.end_date,
            status=new_promotion.status,
            applicable_stores=new_promotion.applicable_stores or [],
            created_at=str(new_promotion.created_at) if new_promotion.created_at else None,
        )


@router.get("/{promotion_id}", response_model=PromotionResponse)
async def get_promotion(
    promotion_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get a specific promotion"""
    async with async_session() as session:
        result = await session.execute(
            select(Promotion).where(Promotion.id == UUID(promotion_id))
        )
        promotion = result.scalar_one_or_none()

        if not promotion:
            raise HTTPException(status_code=404, detail="Promotion not found")

        return PromotionResponse(
            id=str(promotion.id),
            code=promotion.code,
            name=promotion.name,
            description=promotion.description,
            type=promotion.type,
            value=float(promotion.value) if promotion.value else None,
            min_order_amount=float(promotion.min_order_amount),
            max_discount=(
                float(promotion.max_discount) if promotion.max_discount else None
            ),
            usage_limit=promotion.usage_limit,
            used_count=promotion.used_count,
            start_date=promotion.start_date,
            end_date=promotion.end_date,
            status=promotion.status,
            applicable_stores=promotion.applicable_stores or [],
            created_at=str(promotion.created_at) if promotion.created_at else None,
        )


@router.put("/{promotion_id}", response_model=PromotionResponse)
async def update_promotion(
    promotion_id: str,
    promotion: PromotionUpdate,
    current_user: User = Depends(require_auth),
):
    """Update a promotion (owner/admin only)"""
    if current_user.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    async with async_session() as session:
        result = await session.execute(
            select(Promotion).where(Promotion.id == UUID(promotion_id))
        )
        db_promotion = result.scalar_one_or_none()

        if not db_promotion:
            raise HTTPException(status_code=404, detail="Promotion not found")

        # Update fields
        if promotion.name is not None:
            db_promotion.name = promotion.name
        if promotion.description is not None:
            db_promotion.description = promotion.description
        if promotion.value is not None:
            db_promotion.value = promotion.value
        if promotion.min_order_amount is not None:
            db_promotion.min_order_amount = promotion.min_order_amount
        if promotion.max_discount is not None:
            db_promotion.max_discount = promotion.max_discount
        if promotion.usage_limit is not None:
            db_promotion.usage_limit = promotion.usage_limit
        if promotion.start_date is not None:
            db_promotion.start_date = promotion.start_date
        if promotion.end_date is not None:
            db_promotion.end_date = promotion.end_date
        if promotion.applicable_stores is not None:
            db_promotion.applicable_stores = promotion.applicable_stores
        if promotion.status is not None:
            db_promotion.status = promotion.status

        await session.commit()
        await session.refresh(db_promotion)

        return PromotionResponse(
            id=str(db_promotion.id),
            code=db_promotion.code,
            name=db_promotion.name,
            description=db_promotion.description,
            type=db_promotion.type,
            value=float(db_promotion.value) if db_promotion.value else None,
            min_order_amount=float(db_promotion.min_order_amount),
            max_discount=(
                float(db_promotion.max_discount) if db_promotion.max_discount else None
            ),
            usage_limit=db_promotion.usage_limit,
            used_count=db_promotion.used_count,
            start_date=db_promotion.start_date,
            end_date=db_promotion.end_date,
            status=db_promotion.status,
            applicable_stores=db_promotion.applicable_stores or [],
            created_at=str(db_promotion.created_at) if db_promotion.created_at else None,
        )


@router.delete("/{promotion_id}")
async def delete_promotion(
    promotion_id: str,
    current_user: User = Depends(require_auth),
):
    """Delete a promotion (owner/admin only)"""
    if current_user.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    async with async_session() as session:
        result = await session.execute(
            select(Promotion).where(Promotion.id == UUID(promotion_id))
        )
        promotion = result.scalar_one_or_none()

        if not promotion:
            raise HTTPException(status_code=404, detail="Promotion not found")

        await session.delete(promotion)
        await session.commit()

        return {"message": "Promotion deleted successfully"}
