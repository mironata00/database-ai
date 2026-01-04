import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Optional
import logging
from app.utils.encryption import encryption

logger = logging.getLogger(__name__)


class IMAPClientPersonal:
    """IMAP клиент для работы с личной почтой менеджера"""
    
    def __init__(self, host: str, port: int, user: str, password: str, use_ssl: bool = True):
        self.host = host
        self.port = port
        self.user = user
        self.password = encryption.decrypt(password) if password else ""
        self.use_ssl = use_ssl
    
    def connect(self) -> imaplib.IMAP4:
        """Подключение к IMAP серверу"""
        try:
            if self.use_ssl:
                imap = imaplib.IMAP4_SSL(self.host, self.port)
            else:
                imap = imaplib.IMAP4(self.host, self.port)
                imap.starttls()
            
            imap.login(self.user, self.password)
            logger.info(f"Connected to IMAP server {self.host} as {self.user}")
            return imap
        except Exception as e:
            logger.error(f"IMAP connection error for {self.user}: {e}")
            raise
    
    def get_folders(self) -> List[str]:
        """Получение списка папок"""
        imap = None
        try:
            imap = self.connect()
            status, folders_raw = imap.list()
            
            if status != 'OK':
                return ['INBOX']
            
            folder_names = []
            for folder_data in folders_raw:
                if folder_data is None:
                    continue
                    
                try:
                    if isinstance(folder_data, bytes):
                        folder_str = folder_data.decode('utf-8', errors='ignore')
                    else:
                        folder_str = str(folder_data)
                    
                    # Парсим строку вида: (\HasNoChildren) "/" "INBOX"
                    # или (\HasNoChildren) "/" INBOX
                    # или (\Noselect \HasChildren) "/" "[Gmail]"
                    
                    # Ищем последний элемент после разделителя
                    if ' "/" ' in folder_str:
                        parts = folder_str.split(' "/" ')
                        if len(parts) >= 2:
                            folder_name = parts[-1].strip().strip('"')
                            if folder_name and not folder_name.startswith('['):
                                folder_names.append(folder_name)
                    elif ' "." ' in folder_str:
                        parts = folder_str.split(' "." ')
                        if len(parts) >= 2:
                            folder_name = parts[-1].strip().strip('"')
                            if folder_name and not folder_name.startswith('['):
                                folder_names.append(folder_name)
                    elif '"' in folder_str:
                        # Пробуем извлечь имя папки из кавычек
                        import re
                        matches = re.findall(r'"([^"]+)"', folder_str)
                        if matches:
                            folder_name = matches[-1]
                            if folder_name and folder_name not in ['/', '.']:
                                folder_names.append(folder_name)
                                
                except Exception as e:
                    logger.warning(f"Error parsing folder: {folder_data}, error: {e}")
                    continue
            
            # Если папок не найдено, возвращаем стандартный набор
            if not folder_names:
                folder_names = ['INBOX']
            
            # Убираем дубликаты и сортируем
            folder_names = list(dict.fromkeys(folder_names))
            
            # Сортируем: INBOX первый, потом остальные
            def sort_key(name):
                priority = {
                    'INBOX': 0,
                    'Sent': 1,
                    'Drafts': 2,
                    'Trash': 3,
                    'Spam': 4,
                    'Junk': 5,
                }
                lower_name = name.lower()
                for key, val in priority.items():
                    if key.lower() in lower_name:
                        return val
                return 100
            
            folder_names.sort(key=sort_key)
            
            logger.info(f"Found {len(folder_names)} folders: {folder_names}")
            return folder_names
            
        except Exception as e:
            logger.error(f"Error getting folders: {e}")
            return ['INBOX']
        finally:
            if imap:
                try:
                    imap.logout()
                except:
                    pass
    
    def get_messages(
        self, 
        folder: str = "INBOX", 
        limit: int = 50, 
        unread_only: bool = False,
        offset: int = 0
    ) -> List[Dict]:
        """Получение писем из папки"""
        messages = []
        imap = None
        
        try:
            imap = self.connect()
            
            # Пробуем выбрать папку
            try:
                status, _ = imap.select(folder, readonly=True)
            except:
                # Если не получилось, пробуем с кавычками
                status, _ = imap.select(f'"{folder}"', readonly=True)
            
            if status != 'OK':
                logger.warning(f"Could not select folder {folder}")
                return messages
            
            # Поиск писем
            search_criteria = 'UNSEEN' if unread_only else 'ALL'
            status, message_ids = imap.search(None, search_criteria)
            
            if status != 'OK':
                return messages
            
            ids = message_ids[0].split()
            
            # Сортируем по убыванию (новые первые)
            ids = list(reversed(ids))
            
            # Применяем offset и limit
            ids = ids[offset:offset + limit]
            
            for msg_id in ids:
                try:
                    msg_data = self._fetch_message(imap, msg_id)
                    if msg_data:
                        messages.append(msg_data)
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
    
    def _fetch_message(self, imap, msg_id: bytes) -> Optional[Dict]:
        """Получение одного письма"""
        status, header_data = imap.fetch(msg_id, '(BODY.PEEK[HEADER] FLAGS)')
        if status != 'OK':
            return None
        
        flags_raw = header_data[0][0] if header_data[0] else b''
        is_seen = b'\\Seen' in flags_raw
        is_flagged = b'\\Flagged' in flags_raw
        
        header_bytes = header_data[0][1] if len(header_data[0]) > 1 else b''
        email_message = email.message_from_bytes(header_bytes)
        
        subject = self._decode_header(email_message.get('Subject', ''))
        sender = self._decode_header(email_message.get('From', ''))
        to = self._decode_header(email_message.get('To', ''))
        date = email_message.get('Date', '')
        message_id = email_message.get('Message-ID', '')
        
        return {
            'id': msg_id.decode(),
            'message_id': message_id,
            'subject': subject,
            'from': sender,
            'to': to,
            'date': date,
            'is_read': is_seen,
            'is_flagged': is_flagged
        }
    
    def get_message_body(self, folder: str, msg_id: str) -> Dict:
        """Получение полного содержимого письма"""
        imap = None
        
        try:
            imap = self.connect()
            
            try:
                imap.select(folder, readonly=True)
            except:
                imap.select(f'"{folder}"', readonly=True)
            
            status, msg_data = imap.fetch(msg_id.encode(), '(RFC822)')
            
            if status != 'OK':
                return {'error': 'Message not found'}
            
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            
            body_text = ""
            body_html = ""
            attachments = []
            
            if email_message.is_multipart():
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition", ""))
                    
                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        try:
                            charset = part.get_content_charset() or 'utf-8'
                            body_text += part.get_payload(decode=True).decode(charset, errors='ignore')
                        except:
                            pass
                    elif content_type == "text/html" and "attachment" not in content_disposition:
                        try:
                            charset = part.get_content_charset() or 'utf-8'
                            body_html += part.get_payload(decode=True).decode(charset, errors='ignore')
                        except:
                            pass
                    elif "attachment" in content_disposition:
                        filename = part.get_filename()
                        if filename:
                            filename = self._decode_header(filename)
                            attachments.append({
                                'filename': filename,
                                'content_type': content_type,
                                'size': len(part.get_payload(decode=True) or b'')
                            })
            else:
                content_type = email_message.get_content_type()
                try:
                    charset = email_message.get_content_charset() or 'utf-8'
                    payload = email_message.get_payload(decode=True).decode(charset, errors='ignore')
                    if content_type == "text/html":
                        body_html = payload
                    else:
                        body_text = payload
                except:
                    pass
            
            return {
                'id': msg_id,
                'subject': self._decode_header(email_message.get('Subject', '')),
                'from': self._decode_header(email_message.get('From', '')),
                'to': self._decode_header(email_message.get('To', '')),
                'cc': self._decode_header(email_message.get('Cc', '')),
                'date': email_message.get('Date', ''),
                'body_text': body_text,
                'body_html': body_html,
                'attachments': attachments
            }
            
        except Exception as e:
            logger.error(f"Error fetching message body: {e}")
            return {'error': str(e)}
        finally:
            if imap:
                try:
                    imap.close()
                    imap.logout()
                except:
                    pass
    
    def mark_as_read(self, folder: str, msg_id: str) -> bool:
        """Пометить письмо как прочитанное"""
        imap = None
        try:
            imap = self.connect()
            try:
                imap.select(folder)
            except:
                imap.select(f'"{folder}"')
            imap.store(msg_id.encode(), '+FLAGS', '\\Seen')
            return True
        except Exception as e:
            logger.error(f"Error marking message as read: {e}")
            return False
        finally:
            if imap:
                try:
                    imap.close()
                    imap.logout()
                except:
                    pass
    
    def mark_as_unread(self, folder: str, msg_id: str) -> bool:
        """Пометить письмо как непрочитанное"""
        imap = None
        try:
            imap = self.connect()
            try:
                imap.select(folder)
            except:
                imap.select(f'"{folder}"')
            imap.store(msg_id.encode(), '-FLAGS', '\\Seen')
            return True
        except Exception as e:
            logger.error(f"Error marking message as unread: {e}")
            return False
        finally:
            if imap:
                try:
                    imap.close()
                    imap.logout()
                except:
                    pass
    
    def _decode_header(self, value: str) -> str:
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


class IMAPClientLegacy:
    """Легаси клиент для обратной совместимости"""
    
    def __init__(self):
        from app.core.config import settings
        self.host = settings.EMAIL_IMAP_HOST
        self.port = settings.EMAIL_IMAP_PORT
        self.user = settings.EMAIL_IMAP_USER
        self.password = settings.EMAIL_IMAP_PASSWORD
        self.use_ssl = settings.EMAIL_IMAP_USE_SSL
    
    def get_client(self) -> IMAPClientPersonal:
        """Возвращает настроенный клиент"""
        return IMAPClientPersonal(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            use_ssl=self.use_ssl
        )
    
    def get_unread_messages(self, folder: str = "INBOX"):
        """Обратная совместимость"""
        client = self.get_client()
        return client.get_messages(folder=folder, unread_only=True)
    
    def mark_as_read(self, message_id: str, folder: str = "INBOX"):
        """Обратная совместимость"""
        client = self.get_client()
        return client.mark_as_read(folder, message_id)


imap_client = IMAPClientLegacy()
