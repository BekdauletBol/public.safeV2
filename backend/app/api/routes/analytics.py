from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Optional

from app.db.session import get_db
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/realtime")
async def realtime_counts(db: AsyncSession = Depends(get_db)):
    counts = await AnalyticsService.get_realtime_counts(db)
    return {"counts": counts, "timestamp": datetime.utcnow().isoformat()}


@router.get("/camera/{camera_id}/hourly")
async def camera_hourly(
    camera_id: int,
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    end = datetime.utcnow()
    start = end - timedelta(hours=hours)
    data = await AnalyticsService.get_hourly_data(db, camera_id, start, end)
    return {"camera_id": camera_id, "hourly": data}


@router.get("/camera/{camera_id}/daily")
async def camera_daily(
    camera_id: int,
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
):
    data = await AnalyticsService.get_daily_data(db, camera_id, days)
    return {"camera_id": camera_id, "daily": data}


@router.get("/camera/{camera_id}/peaks")
async def camera_peaks(
    camera_id: int,
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
):
    peaks = await AnalyticsService.get_peak_hours(db, camera_id, days)
    return {"camera_id": camera_id, **peaks}


@router.get("/summary/weekly")
async def weekly_summary(db: AsyncSession = Depends(get_db)):
    end = datetime.utcnow()
    start = end - timedelta(days=7)
    summary = await AnalyticsService.get_weekly_summary(db, start, end)
    return summary


@router.post("/record")
async def record_count(
    camera_id: int,
    people_count: int,
    confidence_avg: float = 0.0,
    db: AsyncSession = Depends(get_db),
):
    await AnalyticsService.record_count(db, camera_id, people_count, confidence_avg)
    return {"status": "recorded"}
