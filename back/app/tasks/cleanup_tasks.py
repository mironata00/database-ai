from app.tasks.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="app.tasks.cleanup_tasks.cleanup_old_files")
def cleanup_old_files():
    logger.info("Cleaning up old files")
    # Cleanup logic here
    return {"status": "cleaned", "files_removed": 0}
