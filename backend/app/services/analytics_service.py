from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from loguru import logger

from app.models.analytics import AnalyticsRecord, HourlyAggregate, DailyAggregate
from app.models.camera import Camera


class AnalyticsService:
    @staticmethod
    async def record_count(
        db: AsyncSession,
        camera_id: int,
        people_count: int,
        confidence_avg: float = 0.0,
    ):
        record = AnalyticsRecord(
            camera_id=camera_id,
            people_count=people_count,
            confidence_avg=confidence_avg,
            period_type="realtime",
        )
        db.add(record)
        await db.flush()

    @staticmethod
    async def get_realtime_counts(db: AsyncSession) -> Dict[int, int]:
        cutoff = datetime.utcnow() - timedelta(seconds=10)
        result = await db.execute(
            select(
                AnalyticsRecord.camera_id,
                func.avg(AnalyticsRecord.people_count).label("avg_count"),
            )
            .where(AnalyticsRecord.timestamp >= cutoff)
            .group_by(AnalyticsRecord.camera_id)
        )
        return {row.camera_id: int(row.avg_count) for row in result}

    @staticmethod
    async def get_hourly_data(
        db: AsyncSession,
        camera_id: int,
        start: datetime,
        end: datetime,
    ) -> List[Dict]:
        result = await db.execute(
            select(
                func.date_trunc("hour", AnalyticsRecord.timestamp).label("hour"),
                func.avg(AnalyticsRecord.people_count).label("avg"),
                func.max(AnalyticsRecord.people_count).label("max"),
                func.sum(AnalyticsRecord.people_count).label("total"),
                func.count(AnalyticsRecord.id).label("samples"),
            )
            .where(
                and_(
                    AnalyticsRecord.camera_id == camera_id,
                    AnalyticsRecord.timestamp >= start,
                    AnalyticsRecord.timestamp <= end,
                )
            )
            .group_by(func.date_trunc("hour", AnalyticsRecord.timestamp))
            .order_by(func.date_trunc("hour", AnalyticsRecord.timestamp))
        )
        rows = result.all()
        return [
            {
                "hour": row.hour.isoformat() if row.hour else None,
                "avg": round(float(row.avg), 2) if row.avg else 0,
                "max": row.max or 0,
                "total": row.total or 0,
                "samples": row.samples or 0,
            }
            for row in rows
        ]

    @staticmethod
    async def get_daily_data(
        db: AsyncSession,
        camera_id: int,
        days: int = 7,
    ) -> List[Dict]:
        start = datetime.utcnow() - timedelta(days=days)
        result = await db.execute(
            select(
                func.date_trunc("day", AnalyticsRecord.timestamp).label("day"),
                func.avg(AnalyticsRecord.people_count).label("avg"),
                func.max(AnalyticsRecord.people_count).label("max"),
                func.sum(AnalyticsRecord.people_count).label("total"),
            )
            .where(
                and_(
                    AnalyticsRecord.camera_id == camera_id,
                    AnalyticsRecord.timestamp >= start,
                )
            )
            .group_by(func.date_trunc("day", AnalyticsRecord.timestamp))
            .order_by(func.date_trunc("day", AnalyticsRecord.timestamp))
        )
        rows = result.all()
        return [
            {
                "date": row.day.strftime("%Y-%m-%d") if row.day else None,
                "avg": round(float(row.avg), 2) if row.avg else 0,
                "max": row.max or 0,
                "total": row.total or 0,
            }
            for row in rows
        ]

    @staticmethod
    async def get_peak_hours(db: AsyncSession, camera_id: int, days: int = 7) -> Dict:
        start = datetime.utcnow() - timedelta(days=days)
        result = await db.execute(
            select(
                func.extract("hour", AnalyticsRecord.timestamp).label("hour"),
                func.avg(AnalyticsRecord.people_count).label("avg_count"),
            )
            .where(
                and_(
                    AnalyticsRecord.camera_id == camera_id,
                    AnalyticsRecord.timestamp >= start,
                )
            )
            .group_by(func.extract("hour", AnalyticsRecord.timestamp))
            .order_by(func.avg(AnalyticsRecord.people_count).desc())
        )
        rows = result.all()
        peak_hours = [{"hour": int(row.hour), "avg": round(float(row.avg_count), 2)} for row in rows]
        return {
            "peak_hours": peak_hours[:3],
            "distribution": peak_hours,
        }

    @staticmethod
    async def get_weekly_summary(
        db: AsyncSession,
        start: datetime,
        end: datetime,
    ) -> Dict:
        cameras_result = await db.execute(select(Camera).where(Camera.is_active == True))
        cameras = cameras_result.scalars().all()

        summary = {
            "total_cameras": len(cameras),
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
            "cameras": [],
            "total_traffic": 0,
            "peak_hour": None,
        }

        all_hour_data = []

        for camera in cameras:
            hourly = await AnalyticsService.get_hourly_data(db, camera.id, start, end)
            peaks = await AnalyticsService.get_peak_hours(db, camera.id, 7)
            total = sum(h["total"] for h in hourly)
            avg = round(sum(h["avg"] for h in hourly) / len(hourly), 2) if hourly else 0.0
            max_count = max((h["max"] for h in hourly), default=0)

            summary["cameras"].append({
                "camera_id": camera.id,
                "camera_name": camera.name,
                "address": camera.address,
                "total_traffic": total,
                "avg_count": avg,
                "max_count": max_count,
                "hourly_breakdown": hourly,
                "peak_hours": peaks["peak_hours"],
            })
            summary["total_traffic"] += total
            all_hour_data.extend(peaks["distribution"])

        if all_hour_data:
            peak = max(all_hour_data, key=lambda x: x["avg"])
            summary["peak_hour"] = peak["hour"]

        return summary

    @staticmethod
    async def reset_weekly_stats(db: AsyncSession, before: datetime):
        from sqlalchemy import delete
        await db.execute(
            delete(AnalyticsRecord).where(AnalyticsRecord.timestamp < before)
        )
        await db.commit()
        logger.info(f"Weekly stats reset: deleted records before {before}")
