from app.tasks.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="app.tasks.search_tasks.full_reindex")
def full_reindex():
    logger.info("Starting full Elasticsearch reindex")
    # Reindex logic here
    return {"status": "completed"}
