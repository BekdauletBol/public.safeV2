from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "publicsafe",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "weekly-report-sunday": {
            "task": "app.workers.tasks.generate_weekly_report",
            "schedule": 604800,  # 7 days
        },
        "hourly-aggregation": {
            "task": "app.workers.tasks.run_hourly_aggregation",
            "schedule": 3600,
        },
    },
)
