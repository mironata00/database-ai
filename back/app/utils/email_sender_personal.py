import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict
import logging
from app.utils.encryption import encryption

logger = logging.getLogger(__name__)


def send_email_from_user(
    user_smtp_config: Dict,
    to_email: str,
    subject: str,
    body: str,
    reply_to: str = None
) -> Dict:
    """
    Отправка email с личной почты менеджера.
    Автоматически дешифрует пароль если он зашифрован.
    
    user_smtp_config = {
        'host': 'smtp.jino.ru',
        'port': 587,
        'user': 'info@database-ai.ru',
        'password': 'enc:gAAA...' или 'plain_password',
        'use_tls': True,
        'from_name': 'Иван Иванов',
        'from_email': 'info@database-ai.ru'
    }
    """
    try:
        # Дешифруем пароль если он зашифрован
        password = encryption.decrypt(user_smtp_config['password'])
        
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{user_smtp_config['from_name']} <{user_smtp_config['from_email']}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        
        if reply_to:
            msg['Reply-To'] = reply_to
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Подключение к SMTP
        if user_smtp_config.get('use_tls', True):
            server = smtplib.SMTP(user_smtp_config['host'], user_smtp_config['port'])
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(user_smtp_config['host'], user_smtp_config['port'])
        
        server.login(user_smtp_config['user'], password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email sent to {to_email} from {user_smtp_config['from_email']}")
        
        return {
            "success": True,
            "from_email": user_smtp_config['from_email'],
            "to_email": to_email
        }
        
    except Exception as e:
        logger.error(f"Failed to send email from {user_smtp_config.get('from_email')}: {e}")
        raise Exception(f"Failed to send email: {str(e)}")
