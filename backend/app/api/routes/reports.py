import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List

from app.db.session import get_db
from app.models.report import Report
from app.services.report_service import create_weekly_report
from app.core.security import get_current_user

router = APIRouter()


@router.get("/")
async def list_reports(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).order_by(desc(Report.created_at)))
    reports = result.scalars().all()
    return [
        {
            "id": r.id,
            "title": r.title,
            "report_type": r.report_type,
            "period_start": r.period_start.isoformat(),
            "period_end": r.period_end.isoformat(),
            "status": r.status,
            "file_format": r.file_format,
            "created_at": r.created_at.isoformat(),
            "download_url": f"/api/reports/{r.id}/download" if r.status == "ready" else None,
        }
        for r in reports
    ]


@router.post("/generate", status_code=202)
async def trigger_report(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    report = await create_weekly_report(db)
    return {"message": "Report generated", "report_id": report.id}


@router.get("/{report_id}/download")
async def download_report(report_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.status != "ready":
        raise HTTPException(status_code=400, detail="Report not ready")
    if not report.file_path or not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report file not found")

    media_type = "application/pdf" if report.file_format == "pdf" else "text/csv"
    return FileResponse(
        path=report.file_path,
        media_type=media_type,
        filename=os.path.basename(report.file_path),
    )


@router.get("/{report_id}")
async def get_report(report_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return {
        "id": report.id,
        "title": report.title,
        "status": report.status,
        "ai_insights": report.ai_insights,
        "period_start": report.period_start.isoformat(),
        "period_end": report.period_end.isoformat(),
        "created_at": report.created_at.isoformat(),
    }
