"""
Reports API for admin moderation
"""

import uuid
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, or_
from sqlalchemy.dialects.postgresql import UUID

from src.database import async_session
from src.models.report import Report
from src.models.user import User
from src.middleware.auth_middleware import get_current_user, require_auth

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


class ReportCreate(BaseModel):
    type: str = Field(..., pattern="^(store|product|user|order)$")
    target_id: str
    target_name: str
    reason: str = Field(..., pattern="^(fake_products|wrong_price|harassment|scam|spam|inappropriate)$")
    description: str = Field(..., min_length=10)
    evidence: Optional[List[str]] = None


class ReportUpdate(BaseModel):
    status: Optional[str] = None
    resolution_notes: Optional[str] = None


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
    evidence: Optional[List[str]]
    resolution_notes: Optional[str]
    resolved_by: Optional[str]
    resolved_at: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=List[ReportResponse])
async def list_reports(
    status: Optional[str] = None,
    type_filter: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """List all reports (admin only)"""
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
        
        result = await session.execute(query)
        reports = result.scalars().all()
        
        return [
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
                resolved_at=r.resolved_at,
                created_at=r.created_at,
            )
            for r in reports
        ]


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
            resolved_at=new_report.resolved_at,
            created_at=new_report.created_at,
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
            resolved_at=report.resolved_at,
            created_at=report.created_at,
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
            resolved_at=db_report.resolved_at,
            created_at=db_report.created_at,
        )
