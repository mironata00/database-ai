from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "database_ai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    task_hard_time_limit=settings.CELERY_TASK_HARD_TIME_LIMIT,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "app.tasks.email_tasks.*": {"queue": "email_queue"},
        "app.tasks.parsing_tasks.*": {"queue": "parsing_queue"},
        "app.tasks.search_tasks.*": {"queue": "search_queue"},
    },
)

celery_app.conf.beat_schedule = {
    "check-imap-emails": {
        "task": "app.tasks.email_tasks.check_imap_inbox",
        "schedule": settings.CELERY_BEAT_IMAP_CHECK_INTERVAL,
    },
    "reindex-elasticsearch": {
        "task": "app.tasks.search_tasks.full_reindex",
        "schedule": crontab(hour=2, minute=0),
    },
    "cleanup-old-files": {
        "task": "app.tasks.cleanup_tasks.cleanup_old_files",
        "schedule": settings.CELERY_BEAT_CLEANUP_OLD_FILES_INTERVAL,
    },
}

celery_app.autodiscover_tasks(["app.tasks"])
