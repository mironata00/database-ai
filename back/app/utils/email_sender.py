import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
import logging
import time
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self):
        self.accounts = settings.EMAIL_SMTP_ACCOUNTS
    
    def get_account_by_index(self, index: int):
        """Получить аккаунт по индексу с ротацией"""
        if not self.accounts:
            raise Exception("No SMTP accounts configured")
        return self.accounts[index % len(self.accounts)]
    
    def send_email(self, to_emails: List[str], subject: str, body: str, reply_to: str = None, account_index: int = 0) -> dict:
        """
        Отправка email с указанного аккаунта
        account_index - индекс аккаунта для отправки
        """
        account = self.get_account_by_index(account_index)
        
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{account['from_name']} <{account['from_email']}>"
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            if reply_to:
                msg['Reply-To'] = reply_to
            else:
                msg['Reply-To'] = settings.PRICE_REQUEST_REPLY_TO_EMAIL
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            if account['use_tls']:
                server = smtplib.SMTP(account['host'], account['port'])
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(account['host'], account['port'])
            
            server.login(account['user'], account['password'])
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent to {to_emails} via account {account['id']} ({account['from_email']})")
            
            if settings.PRICE_REQUEST_DELAY_BETWEEN_EMAILS > 0:
                time.sleep(settings.PRICE_REQUEST_DELAY_BETWEEN_EMAILS)
            
            return {
                "success": True,
                "account_id": account['id'],
                "account_email": account['from_email'],
                "recipients": to_emails
            }
            
        except Exception as e:
            logger.error(f"Failed to send email via account {account['id']}: {str(e)}")
            raise Exception(f"Failed to send email: {str(e)}")

email_sender = EmailSender()
