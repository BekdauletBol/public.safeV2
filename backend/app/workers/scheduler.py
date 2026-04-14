import asyncio
from datetime import datetime, timedelta
import pytz
from loguru import logger

from app.db.session import AsyncSessionLocal
from app.services.report_service import create_weekly_report
from app.services.analytics_service import AnalyticsService


async def run_weekly_report():
    async with AsyncSessionLocal() as db:
        try:
            report = await create_weekly_report(db)
            logger.info(f"Scheduled weekly report created: {report.id}")
        except Exception as e:
            logger.error(f"Weekly report failed: {e}")


async def run_hourly_aggregation():
    async with AsyncSessionLocal() as db:
        try:
            logger.info("Running hourly aggregation...")
        except Exception as e:
            logger.error(f"Hourly aggregation failed: {e}")


def is_sunday_2359():
    now = datetime.utcnow()
    return now.weekday() == 6 and now.hour == 23 and now.minute == 59


def is_new_hour(last_hour: int) -> bool:
    return datetime.utcnow().hour != last_hour


async def start_scheduler():
    last_report_week = -1
    last_hour = -1

    logger.info("Background scheduler started")

    while True:
        try:
            now = datetime.utcnow()

            if is_sunday_2359():
                week_num = now.isocalendar()[1]
                if week_num != last_report_week:
                    logger.info("Triggering weekly report (Sunday 23:59)")
                    await run_weekly_report()
                    last_report_week = week_num

            if is_new_hour(last_hour):
                await run_hourly_aggregation()
                last_hour = now.hour

        except Exception as e:
            logger.error(f"Scheduler error: {e}")

        await asyncio.sleep(30)
