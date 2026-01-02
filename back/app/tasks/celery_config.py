from celery.schedules import crontab
from app.core.config import settings

# Базовая конфигурация Celery
broker_url = settings.CELERY_BROKER_URL
result_backend = settings.CELERY_RESULT_BACKEND
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True

# Роутинг задач по очередям
task_routes = {
    'app.tasks.email_tasks.*': {'queue': 'email_queue'},
    'app.tasks.parsing_tasks.*': {'queue': 'parsing_queue'},
    'app.tasks.search_tasks.*': {'queue': 'search_queue'},
    'app.tasks.auto_supplier_tasks.*': {'queue': 'email_queue'},
}

# Расписание задач (beat)
beat_schedule = {
    'check-imap-inbox': {
        'task': 'app.tasks.email_tasks.check_imap_inbox',
        'schedule': settings.CELERY_BEAT_IMAP_CHECK_INTERVAL,
        'options': {'queue': 'email_queue'},
    },
    'full-reindex-elasticsearch': {
        'task': 'app.tasks.search_tasks.full_reindex',
        'schedule': settings.CELERY_BEAT_ES_REINDEX_INTERVAL,
        'options': {'queue': 'search_queue'},
    },
    'cleanup-old-files': {
        'task': 'app.tasks.cleanup_tasks.cleanup_old_files',
        'schedule': settings.CELERY_BEAT_CLEANUP_OLD_FILES_INTERVAL,
    },
}

# ДОБАВЛЯЕМ process-supplier-emails ТОЛЬКО ЕСЛИ IMAP ВКЛЮЧЕН
if settings.EMAIL_IMAP_ENABLED:
    beat_schedule['process-supplier-emails'] = {
        'task': 'app.tasks.auto_supplier_tasks.process_supplier_emails',
        'schedule': 600.0,  # 10 минут
        'options': {'queue': 'email_queue'},
    }
