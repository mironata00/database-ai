from app.tasks.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="app.tasks.email_tasks.check_imap_inbox")
def check_imap_inbox():
    logger.info("Checking IMAP inbox for new emails")
    # IMAP logic here
    return {"status": "checked", "new_emails": 0}
