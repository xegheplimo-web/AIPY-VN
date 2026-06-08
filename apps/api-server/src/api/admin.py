import difflib
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from src.middleware.auth_middleware import require_auth
from src.models.user import User
from src.models.store_match import StoreMatch
from pydantic import BaseModel
from sqlalchemy import func, select
from src.database import async_session
from src.models.order import Order
from src.models.store import Product, Store

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
    matches: list[MatchQueueItem]
    total: int


class ApproveMatchResponse(BaseModel):
    match_id: str
    status: str
    message: str


class IndustryItem(BaseModel):
    id: str
    name: str
    slug: str
    description: str | None = None
    store_count: int


class IndustryListResponse(BaseModel):
    industries: list[IndustryItem]


@router.get("/stats", response_model=AdminStatsResponse)
async def admin_stats(current_user: User = Depends(require_auth)):

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
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


def _calc_similarity(a: str, b: str) -> float:
    """Compute normalized similarity between two strings."""
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


@router.get("/match-queue", response_model=MatchQueueResponse)
async def admin_match_queue(
    status_filter: str = Query("pending", alias="status"),
    current_user: User = Depends(require_auth),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    """Get potential matches between registered stores and existing seed data."""
    async with async_session() as session:
        verified_stmt = select(Store).where(Store.location_verified == True)
        unverified_stmt = select(Store).where(Store.location_verified == False)

        verified_result = await session.execute(verified_stmt)
        unverified_result = await session.execute(unverified_stmt)

        verified_stores = verified_result.scalars().all()
        unverified_stores = unverified_result.scalars().all()

        for ustore in unverified_stores:
            best_match = None
            best_score = 0.0
            matched_fields = []

            for vstore in verified_stores:
                name_sim = _calc_similarity(ustore.name, vstore.name)
                addr_sim = _calc_similarity(ustore.address or "", vstore.address or "")
                phone_sim = 1.0 if (ustore.phone and vstore.phone and ustore.phone == vstore.phone) else 0.0
                score = name_sim * 0.5 + addr_sim * 0.3 + phone_sim * 0.2

                fields = []
                if name_sim > 0.6:
                    fields.append("name")
                if addr_sim > 0.6:
                    fields.append("address")
                if phone_sim == 1.0:
                    fields.append("phone")

                if score > best_score:
                    best_score = score
                    best_match = vstore
                    matched_fields = fields

            if best_match and best_score >= 0.3:
                existing_stmt = select(StoreMatch).where(
                    StoreMatch.registered_store_id == ustore.id,
                    StoreMatch.seed_store_id == best_match.id,
                )
                existing_result = await session.execute(existing_stmt)
                existing = existing_result.scalar_one_or_none()

                if not existing:
                    match = StoreMatch(
                        id=uuid.uuid4(),
                        seed_store_id=best_match.id,
                        registered_store_id=ustore.id,
                        similarity_score=best_score,
                        matched_fields=matched_fields,
                        status="pending",
                    )
                    session.add(match)
                    await session.commit()

        all_pending_stmt = select(StoreMatch).where(StoreMatch.status == status_filter)
        all_pending_result = await session.execute(all_pending_stmt)
        all_pending = all_pending_result.scalars().all()

        matches = []
        for m in all_pending:
            matches.append(
                MatchQueueItem(
                    id=str(m.id),
                    seed_store_name=m.seed_store.name if m.seed_store else "",
                    registered_store_name=m.registered_store.name if m.registered_store else "",
                    similarity=float(m.similarity_score),
                    status=m.status,
                    created_at=str(m.created_at) if m.created_at else datetime.now().isoformat(),
                )
            )

        return MatchQueueResponse(matches=matches, total=len(matches))


@router.post("/matches/{match_id}/approve", response_model=ApproveMatchResponse)
async def admin_approve_match(
    match_id: str,
    current_user: User = Depends(require_auth),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    async with async_session() as session:
        stmt = select(StoreMatch).where(StoreMatch.id == uuid.UUID(match_id))
        result = await session.execute(stmt)
        match = result.scalar_one_or_none()

        if not match:
            raise HTTPException(status_code=404, detail="Match not found")

        if match.status != "pending":
            raise HTTPException(status_code=400, detail=f"Match already {match.status}")

        match.status = "approved"
        match.reviewed_by_id = current_user.id
        match.updated_at = datetime.utcnow()

        if match.registered_store:
            match.registered_store.location_verified = True
            match.registered_store.status = "active"

        await session.commit()

        return ApproveMatchResponse(
            match_id=match_id,
            status="approved",
            message="Match approved and store verified successfully",
        )


@router.get("/industries", response_model=IndustryListResponse)
async def admin_list_industries():

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
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
