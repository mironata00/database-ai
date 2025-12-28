"""
Tasks package
Импортируем все Celery tasks для регистрации
"""
from app.tasks.celery_app import celery_app
from app.tasks.parsing_tasks import parse_pricelist_task
from app.tasks.email_tasks import *
from app.tasks.search_tasks import *
from app.tasks.cleanup_tasks import *

__all__ = [
    "celery_app",
    "parse_pricelist_task",
]
