from celery import shared_task
from app.utils.email_sender import email_sender
from app.core.config import settings
from app.core.database import get_db
from sqlalchemy import select, func
import logging

logger = logging.getLogger(__name__)

# Глобальный счетчик для карусели (общий для всех worker)
from app.core.redis_client import redis_client

def get_next_account_index():
    """Получить следующий индекс аккаунта из Redis с учетом карусели"""
    if not settings.PRICE_REQUEST_USE_CAROUSEL or len(settings.EMAIL_SMTP_ACCOUNTS) <= 1:
        return 0
    
    try:
        # Атомарно увеличиваем счетчик в Redis
        count = redis_client.incr('email_carousel_counter')
        # Вычисляем индекс с учетом лимита на аккаунт
        emails_per_account = settings.PRICE_REQUEST_EMAILS_PER_ACCOUNT
        total_accounts = len(settings.EMAIL_SMTP_ACCOUNTS)
        
        # Определяем какой аккаунт использовать
        account_index = (count - 1) // emails_per_account % total_accounts
        
        logger.info(f"Carousel: count={count}, account_index={account_index}, emails_per_account={emails_per_account}")
        return account_index
    except Exception as e:
        logger.error(f"Redis error in carousel, using account 0: {e}")
        return 0

@shared_task(bind=True, max_retries=3)
def send_price_request_email(self, supplier_email: str, supplier_name: str, subject: str, body: str):
    logger.info(f"Sending price request to {supplier_name} ({supplier_email})")
    
    try:
        # Получаем индекс аккаунта для карусели
        account_index = get_next_account_index()
        
        result = email_sender.send_email(
            to_emails=[supplier_email],
            subject=subject,
            body=body,
            account_index=account_index
        )
        
        logger.info(f"Price request sent successfully to {supplier_email} via account {account_index}")
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

@shared_task
def check_imap_inbox():
    logger.info("Checking IMAP inbox for new emails")
    # Заглушка - функционал проверки почты
    return {"status": "checked", "new_emails": 0}
