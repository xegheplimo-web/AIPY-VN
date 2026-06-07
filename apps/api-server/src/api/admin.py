import uuid
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func

from src.db import async_session
from src.models.store import Store, Product, Category
from src.models.user import User
from src.models.order import Order

router = APIRouter(prefix="/api/admin", tags=["Admin"])


class AdminStatsResponse(BaseModel):
    stores: int
    products: int
    users: int
    orders: int
    pending_orders: int
    total_revenue: float


class MatchQueueItem(BaseModel):
    id: str
    seed_store_name: str
    registered_store_name: str
    similarity: float
    status: str
    created_at: str


class MatchQueueResponse(BaseModel):
    matches: List[MatchQueueItem]
    total: int


class ApproveMatchResponse(BaseModel):
    match_id: str
    status: str
    message: str


class IndustryItem(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    store_count: int


class IndustryListResponse(BaseModel):
    industries: List[IndustryItem]


@router.get("/stats", response_model=AdminStatsResponse)
async def admin_stats():
    async with async_session() as session:
        stores_count = await session.execute(select(func.count(Store.id)))
        products_count = await session.execute(select(func.count(Product.id)))
        users_count = await session.execute(select(func.count(User.id)))
        orders_count = await session.execute(select(func.count(Order.id)))
        pending_orders_count = await session.execute(
            select(func.count(Order.id)).where(Order.status == "pending")
        )

        # Calculate total revenue
        revenue_result = await session.execute(
            select(func.sum(Order.total_amount)).where(Order.payment_status == "paid")
        )
        total_revenue = revenue_result.scalar_one() or 0

        return AdminStatsResponse(
            stores=stores_count.scalar_one(),
            products=products_count.scalar_one(),
            users=users_count.scalar_one(),
            orders=orders_count.scalar_one(),
            pending_orders=pending_orders_count.scalar_one(),
            total_revenue=float(total_revenue),
        )


@router.get("/match-queue", response_model=MatchQueueResponse)
async def admin_match_queue(status: str = "pending"):
    # Mock data for now - in real implementation, this would query a matches table
    return MatchQueueResponse(
        matches=[],
        total=0,
    )


@router.post("/matches/{match_id}/approve", response_model=ApproveMatchResponse)
async def admin_approve_match(match_id: str):
    return ApproveMatchResponse(
        match_id=match_id,
        status="approved",
        message="Match approved successfully",
    )


@router.get("/industries", response_model=IndustryListResponse)
async def admin_list_industries():
    async with async_session() as session:
        # Get distinct industries from stores
        stmt = select(Store.industry).where(Store.industry.isnot(None)).distinct()
        result = await session.execute(stmt)
        industries = result.scalars().all()

        items = []
        for idx, industry in enumerate(industries):
            if industry:
                count_stmt = select(func.count(Store.id)).where(
                    Store.industry == industry
                )
                count_result = await session.execute(count_stmt)
                store_count = count_result.scalar_one()

                items.append(
                    IndustryItem(
                        id=str(idx + 1),
                        name=industry,
                        slug=industry.lower().replace(" ", "-"),
                        store_count=store_count,
                    )
                )

        return IndustryListResponse(industries=items)
