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
        self.current_account_index = 0
        self.emails_sent_per_account = {}
    
    def get_next_account(self):
        if not self.accounts:
            raise Exception("No SMTP accounts configured")
        
        if not settings.PRICE_REQUEST_USE_CAROUSEL:
            return self.accounts[0]
        
        max_per_account = settings.PRICE_REQUEST_EMAILS_PER_ACCOUNT
        attempts = 0
        
        while attempts < len(self.accounts):
            account = self.accounts[self.current_account_index % len(self.accounts)]
            account_id = account['id']
            sent_count = self.emails_sent_per_account.get(account_id, 0)
            
            if sent_count < max_per_account:
                return account
            
            self.current_account_index += 1
            attempts += 1
        
        logger.warning("All accounts reached limit, resetting counters")
        self.emails_sent_per_account = {}
        self.current_account_index = 0
        return self.accounts[0]
    
    def send_email(self, to_emails: List[str], subject: str, body: str, reply_to: str = None) -> dict:
        account = self.get_next_account()
        
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
            
            account_id = account['id']
            self.emails_sent_per_account[account_id] = self.emails_sent_per_account.get(account_id, 0) + 1
            
            logger.info(f"Email sent to {to_emails} via account {account_id}")
            
            if settings.PRICE_REQUEST_DELAY_BETWEEN_EMAILS > 0:
                time.sleep(settings.PRICE_REQUEST_DELAY_BETWEEN_EMAILS)
            
            if settings.PRICE_REQUEST_USE_CAROUSEL:
                if self.emails_sent_per_account[account_id] >= settings.PRICE_REQUEST_EMAILS_PER_ACCOUNT:
                    self.current_account_index += 1
            
            return {
                "success": True,
                "account_id": account_id,
                "account_email": account['from_email'],
                "recipients": to_emails,
                "sent_count": self.emails_sent_per_account[account_id]
            }
            
        except Exception as e:
            logger.error(f"Failed to send email via account {account['id']}: {str(e)}")
            
            if settings.PRICE_REQUEST_USE_CAROUSEL and len(self.accounts) > 1:
                self.current_account_index += 1
                return self.send_email(to_emails, subject, body, reply_to)
            
            raise Exception(f"Failed to send email: {str(e)}")

email_sender = EmailSender()
