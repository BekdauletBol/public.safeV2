import asyncio
from app.workers.celery_app import celery_app
from loguru import logger


@celery_app.task(name="app.workers.tasks.generate_weekly_report")
def generate_weekly_report():
    async def _run():
        from app.db.session import AsyncSessionLocal
        from app.services.report_service import create_weekly_report
        async with AsyncSessionLocal() as db:
            report = await create_weekly_report(db)
            return {"report_id": report.id, "status": "created"}

    return asyncio.get_event_loop().run_until_complete(_run())


@celery_app.task(name="app.workers.tasks.run_hourly_aggregation")
def run_hourly_aggregation():
    logger.info("Celery: running hourly aggregation")
    return {"status": "ok"}
