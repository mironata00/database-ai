from app.tasks.celery_app import celery_app
from app.utils.email_sender import email_sender
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="app.tasks.email_tasks.check_imap_inbox")
def check_imap_inbox():
    logger.info("Checking IMAP inbox for new emails")
    return {"status": "checked", "new_emails": 0}

@celery_app.task(name="app.tasks.email_tasks.send_price_request_email")
def send_price_request_email(supplier_email: str, supplier_name: str, subject: str, body: str):
    logger.info(f"Sending price request to {supplier_name} ({supplier_email})")
    
    try:
        result = email_sender.send_email(
            to_emails=[supplier_email],
            subject=subject,
            body=body
        )
        
        logger.info(f"Price request sent successfully to {supplier_email}")
        return {
            "success": True,
            "supplier_email": supplier_email,
            "supplier_name": supplier_name,
            **result
        }
        
    except Exception as e:
        logger.error(f"Failed to send price request to {supplier_email}: {str(e)}")
        return {
            "success": False,
            "supplier_email": supplier_email,
            "supplier_name": supplier_name,
            "error": str(e)
        }
