import smtplib
import imaplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
from typing import Dict, Optional
import logging
import time

from app.utils.encryption import encryption

logger = logging.getLogger(__name__)


def send_email_from_user(
    user_smtp_config: Dict,
    to_email: str,
    subject: str,
    body: str,
    reply_to: str = None,
    save_to_sent: bool = True,
    imap_config: Dict = None
) -> Dict:
    """
    Отправка email с личной почты менеджера.
    Автоматически дешифрует пароль если он зашифрован.
    Сохраняет копию в папку "Отправленные" на IMAP сервере.
    
    user_smtp_config = {
        'host': 'smtp.jino.ru',
        'port': 587,
        'user': 'info@database-ai.ru',
        'password': 'enc:gAAA...' или 'plain_password',
        'use_tls': True,
        'from_name': 'Иван Иванов',
        'from_email': 'info@database-ai.ru'
    }
    
    imap_config = {
        'host': 'mail.jino.ru',
        'port': 993,
        'user': 'info@database-ai.ru',
        'password': 'enc:gAAA...',
        'use_ssl': True
    }
    """
    try:
        # Дешифруем пароль если он зашифрован
        password = encryption.decrypt(user_smtp_config['password'])
        
        # Создаём сообщение
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{user_smtp_config['from_name']} <{user_smtp_config['from_email']}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = f"<{int(time.time())}.{user_smtp_config['from_email']}>"
        
        if reply_to:
            msg['Reply-To'] = reply_to
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Подключение к SMTP и отправка
        if user_smtp_config.get('use_tls', True):
            server = smtplib.SMTP(user_smtp_config['host'], user_smtp_config['port'])
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(user_smtp_config['host'], user_smtp_config['port'])
        
        server.login(user_smtp_config['user'], password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email sent to {to_email} from {user_smtp_config['from_email']}")
        
        # Сохраняем в папку "Отправленные" на IMAP
        if save_to_sent and imap_config:
            try:
                save_to_sent_folder(msg, imap_config)
            except Exception as e:
                logger.warning(f"Failed to save to Sent folder: {e}")
        
        return {
            "success": True,
            "from_email": user_smtp_config['from_email'],
            "to_email": to_email
        }
        
    except Exception as e:
        logger.error(f"Failed to send email from {user_smtp_config.get('from_email')}: {e}")
        raise Exception(f"Failed to send email: {str(e)}")


def save_to_sent_folder(msg: MIMEMultipart, imap_config: Dict) -> bool:
    """
    Сохраняет отправленное письмо в папку "Отправленные" на IMAP сервере.
    """
    try:
        # Дешифруем пароль
        password = encryption.decrypt(imap_config['password'])
        
        # Подключаемся к IMAP
        if imap_config.get('use_ssl', True):
            imap = imaplib.IMAP4_SSL(imap_config['host'], imap_config['port'])
        else:
            imap = imaplib.IMAP4(imap_config['host'], imap_config['port'])
            imap.starttls()
        
        imap.login(imap_config['user'], password)
        
        # Ищем папку "Отправленные" (разные варианты названий)
        sent_folder = find_sent_folder(imap)
        
        if sent_folder:
            # Сохраняем письмо
            msg_bytes = msg.as_bytes()
            imap.append(sent_folder, '\\Seen', None, msg_bytes)
            logger.info(f"Email saved to '{sent_folder}' folder")
        else:
            logger.warning("Sent folder not found on IMAP server")
        
        imap.logout()
        return True
        
    except Exception as e:
        logger.error(f"Error saving to Sent folder: {e}")
        return False


def find_sent_folder(imap: imaplib.IMAP4) -> Optional[str]:
    """
    Находит папку "Отправленные" на IMAP сервере.
    Поддерживает разные варианты названий.
    """
    # Возможные названия папки "Отправленные"
    sent_folder_names = [
        'Sent',
        'INBOX.Sent',
        'Sent Items',
        'Sent Messages',
        '&BB4EQgQ,BEAEMAQyBDsENQQ9BD0LLQ-',  # Отправленные в UTF-7
        'INBOX.&BB4EQgQ,BEAEMAQyBDsENQQ9BD0LLQ-',
        '&BCEEPwRABDEEOwQ1BD0EPQQ7BDUEPg-',  # Отправленные (другой вариант)
        'INBOX.Отправленные',
        'Отправленные',
    ]
    
    try:
        # Получаем список всех папок
        status, folders = imap.list()
        
        if status != 'OK':
            return None
        
        available_folders = []
        for folder in folders:
            if isinstance(folder, bytes):
                try:
                    # Парсим имя папки
                    parts = folder.decode().split(' "/" ')
                    if len(parts) >= 2:
                        folder_name = parts[-1].strip('"')
                        available_folders.append(folder_name)
                except:
                    continue
        
        logger.info(f"Available IMAP folders: {available_folders}")
        
        # Ищем папку по списку возможных названий
        for sent_name in sent_folder_names:
            if sent_name in available_folders:
                return sent_name
        
        # Ищем папку содержащую "Sent" или "sent"
        for folder in available_folders:
            if 'sent' in folder.lower():
                return folder
        
        # Если не нашли, возвращаем стандартную
        return 'Sent'
        
    except Exception as e:
        logger.error(f"Error finding Sent folder: {e}")
        return 'Sent'


def send_email_with_user_model(user, to_email: str, subject: str, body: str, reply_to: str = None) -> Dict:
    """
    Отправка email используя модель User напрямую.
    Автоматически получает SMTP и IMAP конфигурацию из пользователя.
    """
    if not user.has_smtp_configured():
        raise Exception("SMTP не настроен для пользователя")
    
    smtp_config = {
        'host': user.smtp_host,
        'port': user.smtp_port,
        'user': user.smtp_user,
        'password': user.smtp_password,
        'use_tls': user.smtp_use_tls,
        'from_name': user.smtp_from_name or user.full_name or user.smtp_user,
        'from_email': user.smtp_user
    }
    
    imap_config = None
    if user.has_imap_configured():
        imap_config = {
            'host': user.imap_host,
            'port': user.imap_port,
            'user': user.imap_user,
            'password': user.imap_password,
            'use_ssl': user.imap_use_ssl
        }
    
    return send_email_from_user(
        user_smtp_config=smtp_config,
        to_email=to_email,
        subject=subject,
        body=body,
        reply_to=reply_to,
        save_to_sent=True,
        imap_config=imap_config
    )


def send_email_from_user_with_attachments(
    user_smtp_config: Dict,
    to_email: str,
    subject: str,
    body: str,
    attachments: list = None,
    reply_to: str = None,
    save_to_sent: bool = True,
    imap_config: Dict = None
) -> Dict:
    """
    Отправка email с вложениями с личной почты менеджера.
    
    attachments = [
        {
            'filename': 'document.pdf',
            'content': b'...',
            'content_type': 'application/pdf'
        }
    ]
    """
    from email.mime.base import MIMEBase
    from email import encoders
    
    try:
        # Дешифруем пароль
        password = encryption.decrypt(user_smtp_config['password'])

        # Создаём сообщение
        msg = MIMEMultipart()
        msg['From'] = f"{user_smtp_config['from_name']} <{user_smtp_config['from_email']}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = f"<{int(time.time())}.{user_smtp_config['from_email']}>"

        if reply_to:
            msg['Reply-To'] = reply_to
            msg['In-Reply-To'] = reply_to
            msg['References'] = reply_to

        # Добавляем тело письма
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # Добавляем вложения
        if attachments:
            for attachment in attachments:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment['content'])
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename="{attachment["filename"]}"'
                )
                if 'content_type' in attachment:
                    part.set_type(attachment['content_type'])
                msg.attach(part)

        # Подключение к SMTP и отправка
        if user_smtp_config.get('use_tls', True):
            server = smtplib.SMTP(user_smtp_config['host'], user_smtp_config['port'])
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(user_smtp_config['host'], user_smtp_config['port'])

        server.login(user_smtp_config['user'], password)
        server.send_message(msg)
        server.quit()

        logger.info(f"Email with {len(attachments) if attachments else 0} attachments sent to {to_email}")

        # Сохраняем в "Отправленные"
        if save_to_sent and imap_config:
            try:
                save_to_sent_folder(msg, imap_config)
            except Exception as e:
                logger.warning(f"Failed to save to Sent folder: {e}")

        return {
            "success": True,
            "from_email": user_smtp_config['from_email'],
            "to_email": to_email,
            "attachments_count": len(attachments) if attachments else 0
        }

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise Exception(f"Failed to send email: {str(e)}")
