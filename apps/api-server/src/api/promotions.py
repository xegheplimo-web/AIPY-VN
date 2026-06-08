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
from src.models.store import Store
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


async def _get_owner_store_ids(user_id) -> list[str]:
    """
    Get the store IDs owned by a given user.

    Args:
        user_id: The owner's user ID (UUID or string)

    Returns:
        List of store ID strings
    """
    async with async_session() as session:
        query = select(Store.id).where(Store.owner_id == user_id)
        result = await session.execute(query)
        store_ids = result.scalars().all()
        return [str(sid) for sid in store_ids]


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

        # Owners can only see promotions applicable to their stores
        if current_user.role == "owner":
            user_id = current_user.id if hasattr(current_user, "id") else current_user.get("id")
            owner_store_ids = await _get_owner_store_ids(user_id)

            if owner_store_ids:
                # Show promotions where:
                # 1. applicable_stores is empty/null (applies to all stores), OR
                # 2. applicable_stores contains "all" (applies to all stores), OR
                # 3. applicable_stores contains any of the owner's store IDs
                #
                # Since applicable_stores is a JSON column, we filter in Python
                # after the initial query for maximum compatibility across
                # database backends (PostgreSQL JSON, SQLite JSON, etc.).
                pass  # Filtering applied after query execution below
            else:
                # Owner has no stores — return empty list
                metadata = get_pagination_metadata(0, page, limit)
                return PromotionListResponse(
                    promotions=[],
                    total=0,
                    page=page,
                    limit=limit,
                    total_pages=metadata["total_pages"],
                    has_next=metadata["has_next"],
                    has_prev=metadata["has_prev"],
                )

        # Count total (before owner filtering, we will recount after)
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination
        query = query.order_by(Promotion.created_at.desc())
        query = paginate(query, page=page, limit=limit)
        result = await session.execute(query)
        promotions = result.scalars().all()

        # Apply owner store filtering in Python for JSON column compatibility
        if current_user.role == "owner":
            user_id = current_user.id if hasattr(current_user, "id") else current_user.get("id")
            owner_store_ids = await _get_owner_store_ids(user_id)

            if owner_store_ids:
                filtered_promotions = []
                for p in promotions:
                    stores = p.applicable_stores or []
                    # Promotion applies to all stores (empty list, ["all"], or None)
                    if not stores or "all" in stores:
                        filtered_promotions.append(p)
                    else:
                        # Check if any of the owner's store IDs are in the applicable_stores
                        if any(str(sid) in stores for sid in owner_store_ids):
                            filtered_promotions.append(p)
                promotions = filtered_promotions
                total = len(filtered_promotions)

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

        user_id = current_user.id if hasattr(current_user, "id") else current_user.get("id")

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
            created_by=user_id,
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

        # Owners can only view promotions applicable to their stores
        if current_user.role == "owner":
            user_id = current_user.id if hasattr(current_user, "id") else current_user.get("id")
            owner_store_ids = await _get_owner_store_ids(user_id)
            stores = promotion.applicable_stores or []
            if stores and "all" not in stores:
                if not any(str(sid) in stores for sid in owner_store_ids):
                    raise HTTPException(status_code=403, detail="Not authorized to view this promotion")

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

        # Owners can only update promotions applicable to their stores
        if current_user.role == "owner":
            user_id = current_user.id if hasattr(current_user, "id") else current_user.get("id")
            owner_store_ids = await _get_owner_store_ids(user_id)
            stores = db_promotion.applicable_stores or []
            if stores and "all" not in stores:
                if not any(str(sid) in stores for sid in owner_store_ids):
                    raise HTTPException(status_code=403, detail="Not authorized to update this promotion")

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

        # Owners can only delete promotions applicable to their stores
        if current_user.role == "owner":
            user_id = current_user.id if hasattr(current_user, "id") else current_user.get("id")
            owner_store_ids = await _get_owner_store_ids(user_id)
            stores = promotion.applicable_stores or []
            if stores and "all" not in stores:
                if not any(str(sid) in stores for sid in owner_store_ids):
                    raise HTTPException(status_code=403, detail="Not authorized to delete this promotion")

        await session.delete(promotion)
        await session.commit()

        return {"message": "Promotion deleted successfully"}


class ValidatePromotionResponse(BaseModel):
    valid: bool
    discount: float
    type: str
    code: str
    message: str


@router.post("/validate/{code}", response_model=ValidatePromotionResponse)
async def validate_promotion_code(
    code: str,
    order_amount: float = Query(..., ge=0, description="Current order subtotal"),
    store_id: str | None = Query(None, description="Store ID to check applicability"),
):
    """Validate a promotion code against current order amount"""
    async with async_session() as session:
        result = await session.execute(
            select(Promotion).where(Promotion.code == code.upper())
        )
        promotion = result.scalar_one_or_none()

        if not promotion:
            return ValidatePromotionResponse(
                valid=False,
                discount=0,
                type="",
                code=code,
                message="Mã giảm giá không tồn tại",
            )

        if promotion.status != "active":
            return ValidatePromotionResponse(
                valid=False,
                discount=0,
                type=promotion.type,
                code=promotion.code,
                message="Mã giảm giá không còn hiệu lực",
            )

        from datetime import datetime

        now = datetime.now().isoformat()
        if promotion.start_date and now < promotion.start_date:
            return ValidatePromotionResponse(
                valid=False,
                discount=0,
                type=promotion.type,
                code=promotion.code,
                message="Mã giảm giá chưa có hiệu lực",
            )

        if promotion.end_date and now > promotion.end_date:
            return ValidatePromotionResponse(
                valid=False,
                discount=0,
                type=promotion.type,
                code=promotion.code,
                message="Mã giảm giá đã hết hạn",
            )

        if promotion.min_order_amount and order_amount < float(
            promotion.min_order_amount
        ):
            return ValidatePromotionResponse(
                valid=False,
                discount=0,
                type=promotion.type,
                code=promotion.code,
                message=f"Đơn hàng tối thiểu {float(promotion.min_order_amount):,.0f}đ",
            )

        if (
            promotion.usage_limit is not None
            and promotion.used_count >= promotion.usage_limit
        ):
            return ValidatePromotionResponse(
                valid=False,
                discount=0,
                type=promotion.type,
                code=promotion.code,
                message="Mã giảm giá đã hết lượt sử dụng",
            )

        if (
            store_id
            and promotion.applicable_stores
            and "all" not in promotion.applicable_stores
        ):
            if store_id not in promotion.applicable_stores:
                return ValidatePromotionResponse(
                    valid=False,
                    discount=0,
                    type=promotion.type,
                    code=promotion.code,
                    message="Mã giảm giá không áp dụng cho cửa hàng này",
                )

        # Calculate discount
        discount = 0.0
        if promotion.type == "percentage" and promotion.value:
            discount = order_amount * (float(promotion.value) / 100)
            if promotion.max_discount:
                discount = min(discount, float(promotion.max_discount))
        elif promotion.type == "fixed" and promotion.value:
            discount = float(promotion.value)
            if promotion.max_discount:
                discount = min(discount, float(promotion.max_discount))
        elif promotion.type == "free_shipping":
            discount = 0  # Special handling for free shipping

        return ValidatePromotionResponse(
            valid=True,
            discount=discount,
            type=promotion.type,
            code=promotion.code,
            message="Mã giảm giá hợp lệ",
        )
