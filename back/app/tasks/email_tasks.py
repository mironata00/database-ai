from celery import shared_task
from app.utils.email_sender import email_sender
from app.core.config import settings
from app.core.redis_client import redis_client
import logging

logger = logging.getLogger(__name__)

def get_valid_accounts_count():
    """Подсчет РЕАЛЬНЫХ аккаунтов (не заглушек)"""
    valid_count = 0
    for account in settings.EMAIL_SMTP_ACCOUNTS:
        # Проверяем что это не заглушка
        if not account['from_email'].startswith('your-email'):
            valid_count += 1
    return valid_count

def get_next_account_index():
    """Получить следующий индекс аккаунта из Redis с учетом карусели"""
    if not settings.PRICE_REQUEST_USE_CAROUSEL:
        return 0
    
    try:
        # Считаем ТОЛЬКО валидные аккаунты
        total_accounts = get_valid_accounts_count()
        
        if total_accounts == 0:
            logger.error("No valid SMTP accounts found!")
            return 0
        
        emails_per_account = settings.PRICE_REQUEST_EMAILS_PER_ACCOUNT
        
        # Получаем текущий счетчик
        count = redis_client.incr('email_carousel_counter')
        
        # Вычисляем индекс аккаунта (циклично)
        account_index = ((count - 1) // emails_per_account) % total_accounts
        
        logger.info(f"Carousel: count={count}, account_index={account_index}, emails_per_account={emails_per_account}, total_accounts={total_accounts}")
        
        # Если прошли все аккаунты - сбрасываем счетчик
        if count >= total_accounts * emails_per_account:
            redis_client.set('email_carousel_counter', 0)
            logger.info("Carousel: Reset counter after full cycle")
        
        return account_index
        
    except Exception as e:
        logger.error(f"Redis error in carousel, using account 0: {e}")
        return 0

@shared_task(bind=True, max_retries=3)
def send_price_request_email(self, supplier_email: str, supplier_name: str, subject: str, body: str):
    logger.info(f"Sending price request to {supplier_name} ({supplier_email})")
    
    try:
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
    return {"status": "checked", "new_emails": 0}

@shared_task(bind=True, max_retries=3)
def send_price_request_email_personal(self, user_smtp_config: dict, to_email: str, subject: str, body: str, reply_to: str = None):
    """Отправка письма с личной почты менеджера"""
    logger.info(f"Sending email from {user_smtp_config['from_email']} to {to_email}")
    
    try:
        from app.utils.email_sender_personal import send_email_from_user
        
        result = send_email_from_user(
            user_smtp_config=user_smtp_config,
            to_email=to_email,
            subject=subject,
            body=body,
            reply_to=reply_to
        )
        
        logger.info(f"Email sent successfully from {user_smtp_config['from_email']} to {to_email}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to send email from {user_smtp_config['from_email']}: {str(e)}")
        raise self.retry(exc=e, countdown=60)
