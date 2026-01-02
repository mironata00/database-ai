import imaplib
import email
from email.header import decode_header
from typing import List, Dict
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class IMAPClient:
    """Клиент для работы с IMAP"""
    
    def __init__(self):
        self.host = settings.EMAIL_IMAP_HOST
        self.port = settings.EMAIL_IMAP_PORT
        self.user = settings.EMAIL_IMAP_USER
        self.password = settings.EMAIL_IMAP_PASSWORD
        self.use_ssl = settings.EMAIL_IMAP_USE_SSL
    
    def connect(self) -> imaplib.IMAP4_SSL:
        """Подключение к IMAP серверу"""
        try:
            if self.use_ssl:
                imap = imaplib.IMAP4_SSL(self.host, self.port)
            else:
                imap = imaplib.IMAP4(self.host, self.port)
            
            imap.login(self.user, self.password)
            logger.info(f"Connected to IMAP server {self.host}")
            return imap
        except Exception as e:
            logger.error(f"IMAP connection error: {e}")
            raise
    
    def get_unread_messages(self, folder: str = "INBOX") -> List[Dict]:
        """Получение непрочитанных писем"""
        messages = []
        imap = None
        
        try:
            imap = self.connect()
            imap.select(folder)
            
            # Ищем непрочитанные письма
            status, message_ids = imap.search(None, 'UNSEEN')
            
            if status != 'OK':
                logger.warning("No unread messages found")
                return messages
            
            for msg_id in message_ids[0].split():
                try:
                    # Получаем письмо
                    status, msg_data = imap.fetch(msg_id, '(RFC822)')
                    
                    if status != 'OK':
                        continue
                    
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)
                    
                    # Извлекаем данные
                    subject = self.decode_header_value(email_message.get('Subject', ''))
                    sender = self.decode_header_value(email_message.get('From', ''))
                    
                    # Извлекаем тело и вложения
                    body_text = ""
                    attachments = []
                    
                    if email_message.is_multipart():
                        for part in email_message.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition", ""))
                            
                            # Текст письма
                            if content_type == "text/plain" and "attachment" not in content_disposition:
                                try:
                                    body_text += part.get_payload(decode=True).decode()
                                except:
                                    pass
                            
                            # Вложения
                            elif "attachment" in content_disposition:
                                filename = part.get_filename()
                                if filename:
                                    filename = self.decode_header_value(filename)
                                    file_data = part.get_payload(decode=True)
                                    attachments.append({
                                        'filename': filename,
                                        'data': file_data,
                                        'content_type': content_type
                                    })
                    else:
                        body_text = email_message.get_payload(decode=True).decode()
                    
                    messages.append({
                        'id': msg_id.decode(),
                        'subject': subject,
                        'sender': sender,
                        'body': body_text,
                        'attachments': attachments
                    })
                    
                    logger.info(f"Processed email: {subject} from {sender}")
                    
                except Exception as e:
                    logger.error(f"Error processing message {msg_id}: {e}")
                    continue
            
            return messages
            
        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            return messages
        finally:
            if imap:
                try:
                    imap.close()
                    imap.logout()
                except:
                    pass
    
    def mark_as_read(self, message_id: str, folder: str = "INBOX"):
        """Пометить письмо как прочитанное"""
        imap = None
        try:
            imap = self.connect()
            imap.select(folder)
            imap.store(message_id.encode(), '+FLAGS', '\\Seen')
            logger.info(f"Marked message {message_id} as read")
        except Exception as e:
            logger.error(f"Error marking message as read: {e}")
        finally:
            if imap:
                try:
                    imap.close()
                    imap.logout()
                except:
                    pass
    
    def decode_header_value(self, value: str) -> str:
        """Декодирование заголовка письма"""
        if not value:
            return ""
        
        decoded_parts = decode_header(value)
        decoded_string = ""
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_string += part.decode(encoding or 'utf-8', errors='ignore')
            else:
                decoded_string += part
        
        return decoded_string

imap_client = IMAPClient()
