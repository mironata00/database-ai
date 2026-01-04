"""
Задачи для автоматической обработки поставщиков
"""
from celery import shared_task
from sqlalchemy import select
from app.core.database import get_sync_db
from app.models.user import User
from app.models.supplier import Supplier
from app.utils.imap_client import IMAPClientPersonal
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)


@shared_task(name="check_supplier_emails")
def check_supplier_emails():
    """Проверка новых писем от поставщиков"""
    logger.info("Checking supplier emails...")
    # TODO: Реализация проверки писем
    return {"status": "ok", "message": "Check completed"}


@shared_task(name="process_supplier_emails", bind=True)
def process_supplier_emails(self):
    """
    Обработка писем от поставщиков с прайс-листами
    Автоматическое создание поставщиков из писем
    """
    logger.info("Starting email processing task...")

    try:
        db = next(get_sync_db())

        # Получаем всех админов с настроенным IMAP
        result = db.execute(
            select(User).where(
                User.role == 'admin',
                User.imap_host.isnot(None),
                User.imap_user.isnot(None)
            )
        )
        users = result.scalars().all()

        if not users:
            logger.warning("No users with IMAP configured")
            return {"processed": 0, "message": "No users with IMAP"}

        total_processed = 0

        for user in users:
            try:
                logger.info(f"Processing emails for user {user.email}")

                # Подключаемся к IMAP
                client = IMAPClientPersonal(
                    host=user.imap_host,
                    port=user.imap_port,
                    user=user.imap_user,
                    password=user.imap_password,
                    use_ssl=user.imap_use_ssl
                )

                # Получаем непрочитанные письма из INBOX
                messages = client.get_messages(
                    folder='INBOX',
                    limit=50,
                    unread_only=True
                )

                logger.info(f"Found {len(messages)} unread messages")

                for msg in messages:
                    # Проверяем есть ли вложения (прайс-листы)
                    if msg.get('has_attachments'):
                        # Извлекаем email отправителя
                        from_email = extract_email(msg['from'])

                        # Проверяем существует ли поставщик с таким email
                        existing = db.execute(
                            select(Supplier).where(Supplier.email == from_email)
                        ).scalar_one_or_none()

                        if not existing:
                            logger.info(f"New potential supplier: {from_email}")
                            # TODO: Создать поставщика в статусе PENDING
                            # Пока просто логируем

                        total_processed += 1

            except Exception as e:
                logger.error(f"Error processing emails for user {user.email}: {str(e)}")
                continue

        db.close()

        return {
            "processed": total_processed,
            "message": f"Processed {total_processed} emails"
        }

    except Exception as e:
        logger.error(f"Error in process_supplier_emails: {str(e)}")
        raise


def extract_email(from_str: str) -> str:
    """Извлечь email из строки 'Name <email@example.com>'"""
    if not from_str:
        return ""
    
    match = re.search(r'<(.+?)>', from_str)
    if match:
        return match.group(1).lower()
    return from_str.lower()
