"""
Reports API for admin moderation
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import UUID
from src.database import async_session
from src.middleware.auth_middleware import get_current_user, require_auth
from src.models.report import Report
from src.models.user import User
from src.utils.pagination import paginate, get_pagination_metadata

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


class ReportCreate(BaseModel):
    type: str = Field(..., pattern="^(store|product|user|order)$")
    target_id: str
    target_name: str
    reason: str = Field(
        ..., pattern="^(fake_products|wrong_price|harassment|scam|spam|inappropriate)$"
    )
    description: str = Field(..., min_length=10)
    evidence: list[str] | None = None


class ReportUpdate(BaseModel):
    status: str | None = None
    resolution_notes: str | None = None


class ReportResponse(BaseModel):
    id: str
    type: str
    target_id: str
    target_name: str
    reporter_id: str
    reporter_name: str
    reason: str
    description: str
    status: str
    evidence: list[str] | None
    resolution_notes: str | None
    resolved_by: str | None
    resolved_at: str | None
    created_at: str

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """Response model for report list with pagination."""

    reports: list[ReportResponse]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool


@router.get("", response_model=ReportListResponse)
async def list_reports(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = None,
    type_filter: str | None = None,
    search: str | None = None,
    current_user: User = Depends(get_current_user),
):
    """List all reports with pagination (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    async with async_session() as session:
        query = select(Report)

        if status:
            query = query.where(Report.status == status)

        if type_filter:
            query = query.where(Report.type == type_filter)

        if search:
            query = query.where(
                or_(
                    Report.target_name.ilike(f"%{search}%"),
                    Report.reporter_name.ilike(f"%{search}%"),
                    Report.description.ilike(f"%{search}%"),
                )
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination
        query = query.order_by(Report.created_at.desc())
        query = paginate(query, page=page, limit=limit)
        result = await session.execute(query)
        reports = result.scalars().all()

        # Get pagination metadata
        metadata = get_pagination_metadata(total, page, limit)

        return ReportListResponse(
            reports=[
                ReportResponse(
                    id=str(r.id),
                    type=r.type,
                    target_id=str(r.target_id),
                    target_name=r.target_name,
                    reporter_id=str(r.reporter_id),
                    reporter_name=r.reporter_name,
                    reason=r.reason,
                    description=r.description,
                    status=r.status,
                    evidence=r.evidence,
                    resolution_notes=r.resolution_notes,
                    resolved_by=str(r.resolved_by) if r.resolved_by else None,
                    resolved_at=str(r.resolved_at) if r.resolved_at else None,
                    created_at=str(r.created_at) if r.created_at else None,
                )
                for r in reports
            ],
            total=total,
            page=page,
            limit=limit,
            total_pages=metadata["total_pages"],
            has_next=metadata["has_next"],
            has_prev=metadata["has_prev"],
        )


@router.post("", response_model=ReportResponse, status_code=201)
async def create_report(
    report: ReportCreate,
    current_user: User = Depends(require_auth),
):
    """Create a new report"""
    async with async_session() as session:
        new_report = Report(
            id=uuid.uuid4(),
            type=report.type,
            target_id=UUID(report.target_id),
            target_name=report.target_name,
            reporter_id=current_user.id,
            reporter_name=current_user.full_name or current_user.email,
            reason=report.reason,
            description=report.description,
            evidence=report.evidence,
            status="pending",
        )

        session.add(new_report)
        await session.commit()
        await session.refresh(new_report)

        return ReportResponse(
            id=str(new_report.id),
            type=new_report.type,
            target_id=str(new_report.target_id),
            target_name=new_report.target_name,
            reporter_id=str(new_report.reporter_id),
            reporter_name=new_report.reporter_name,
            reason=new_report.reason,
            description=new_report.description,
            status=new_report.status,
            evidence=new_report.evidence,
            resolution_notes=new_report.resolution_notes,
            resolved_by=str(new_report.resolved_by) if new_report.resolved_by else None,
            resolved_at=str(new_report.resolved_at) if new_report.resolved_at else None,
            created_at=str(new_report.created_at) if new_report.created_at else None,
        )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get a specific report"""
    async with async_session() as session:
        result = await session.execute(
            select(Report).where(Report.id == UUID(report_id))
        )
        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        return ReportResponse(
            id=str(report.id),
            type=report.type,
            target_id=str(report.target_id),
            target_name=report.target_name,
            reporter_id=str(report.reporter_id),
            reporter_name=report.reporter_name,
            reason=report.reason,
            description=report.description,
            status=report.status,
            evidence=report.evidence,
            resolution_notes=report.resolution_notes,
            resolved_by=str(report.resolved_by) if report.resolved_by else None,
            resolved_at=str(report.resolved_at) if report.resolved_at else None,
            created_at=str(report.created_at) if report.created_at else None,
        )


@router.put("/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: str,
    report: ReportUpdate,
    current_user: User = Depends(require_auth),
):
    """Update a report (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    async with async_session() as session:
        result = await session.execute(
            select(Report).where(Report.id == UUID(report_id))
        )
        db_report = result.scalar_one_or_none()

        if not db_report:
            raise HTTPException(status_code=404, detail="Report not found")

        if report.status is not None:
            db_report.status = report.status
            if report.status in ["resolved", "dismissed"]:
                db_report.resolved_by = current_user.id
                db_report.resolved_at = datetime.now().isoformat()

        if report.resolution_notes is not None:
            db_report.resolution_notes = report.resolution_notes

        await session.commit()
        await session.refresh(db_report)

        return ReportResponse(
            id=str(db_report.id),
            type=db_report.type,
            target_id=str(db_report.target_id),
            target_name=db_report.target_name,
            reporter_id=str(db_report.reporter_id),
            reporter_name=db_report.reporter_name,
            reason=db_report.reason,
            description=db_report.description,
            status=db_report.status,
            evidence=db_report.evidence,
            resolution_notes=db_report.resolution_notes,
            resolved_by=str(db_report.resolved_by) if db_report.resolved_by else None,
            resolved_at=str(db_report.resolved_at) if db_report.resolved_at else None,
            created_at=str(db_report.created_at) if db_report.created_at else None,
        )
