"""
IMAP Client для работы с почтой пользователя
"""
import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Optional, Tuple
import logging
import re

logger = logging.getLogger(__name__)


class IMAPClientPersonal:
    def __init__(self, host: str, port: int, user: str, password: str, use_ssl: bool = True):
        from app.utils.encryption import encryption
        self.host = host
        self.port = port
        self.user = user
        self.password = encryption.decrypt(password) if password else password
        self.use_ssl = use_ssl
        self.connection = None

    def connect(self):
        """Подключение к IMAP серверу"""
        try:
            if self.use_ssl:
                self.connection = imaplib.IMAP4_SSL(self.host, self.port)
            else:
                self.connection = imaplib.IMAP4(self.host, self.port)
            self.connection.login(self.user, self.password)
            logger.info(f"Connected to IMAP server {self.host} as {self.user}")
            return True
        except Exception as e:
            logger.error(f"IMAP connection error: {str(e)}")
            raise

    def disconnect(self):
        """Отключение от IMAP"""
        if self.connection:
            try:
                self.connection.logout()
            except:
                pass

    def get_folders(self) -> List[str]:
        """Получить список папок в правильном порядке"""
        try:
            self.connect()
            status, folders = self.connection.list()
            if status != 'OK':
                logger.error(f"Failed to get folders: {status}")
                return ['INBOX']
            folder_list = []
            for folder in folders:
                try:
                    if isinstance(folder, bytes):
                        folder_str = folder.decode('utf-8', errors='ignore')
                    else:
                        folder_str = str(folder)
                    logger.info(f"Raw folder line: {folder_str}")
                    match = re.search(r'["\']([^"\']+)["\']$', folder_str)
                    if match:
                        folder_name = match.group(1)
                    else:
                        parts = folder_str.split()
                        if len(parts) >= 3:
                            folder_name = parts[-1].strip('"\'')
                        else:
                            continue
                    if folder_name and folder_name not in ['', '.', '..']:
                        folder_list.append(folder_name)
                        logger.info(f"Added folder: {folder_name}")
                except Exception as e:
                    logger.error(f"Error parsing folder: {e}")
                    continue
            self.disconnect()
            if not folder_list:
                logger.warning("No folders found, returning default INBOX")
                folder_list = ['INBOX']
            folder_list = self._sort_folders(folder_list)
            logger.info(f"Total folders found: {len(folder_list)} - {folder_list}")
            return folder_list
        except Exception as e:
            logger.error(f"Error getting folders: {str(e)}")
            self.disconnect()
            return ['INBOX']

    def _sort_folders(self, folders: List[str]) -> List[str]:
        """Сортировка папок в правильном порядке"""
        priority_order = {
            'INBOX': 0, 'Входящие': 0, 'Sent': 1, 'Отправленные': 1,
            'Spam': 2, 'Спам': 2, 'Junk': 2, 'Trash': 3, 'Корзина': 3,
            'Deleted': 3, 'Quarantine': 4, 'Карантин': 4, 'Drafts': 5, 'Черновики': 5,
        }
        def get_priority(folder_name: str) -> int:
            if folder_name in priority_order:
                return priority_order[folder_name]
            folder_lower = folder_name.lower()
            for key, priority in priority_order.items():
                if key.lower() in folder_lower or folder_lower in key.lower():
                    return priority
            return 999
        sorted_folders = sorted(folders, key=lambda f: (get_priority(f), f))
        return sorted_folders

    def get_messages(self, folder: str = "INBOX", limit: int = 50, offset: int = 0, unread_only: bool = False) -> List[Dict]:
        """Получить список сообщений из папки"""
        try:
            self.connect()
            status, data = self.connection.select(f'"{folder}"', readonly=True)
            if status != 'OK':
                logger.error(f"Failed to select folder {folder}: {status}")
                self.disconnect()
                return []
            search_criteria = 'UNSEEN' if unread_only else 'ALL'
            status, messages = self.connection.search(None, search_criteria)
            if status != 'OK':
                self.disconnect()
                return []
            message_ids = messages[0].split()
            message_ids.reverse()
            message_ids = message_ids[offset:offset + limit]
            result = []
            for msg_id in message_ids:
                try:
                    status, msg_data = self.connection.fetch(msg_id, '(RFC822.HEADER FLAGS)')
                    if status != 'OK':
                        continue
                    raw_email = msg_data[0][1]
                    email_message = email.message_from_bytes(raw_email)
                    flags_str = str(msg_data[0][0])
                    is_read = '\\Seen' in flags_str
                    is_flagged = '\\Flagged' in flags_str
                    subject = self._decode_header(email_message.get('Subject', ''))
                    from_addr = self._decode_header(email_message.get('From', ''))
                    to_addr = self._decode_header(email_message.get('To', ''))
                    date = email_message.get('Date', '')
                    # Проверяем наличие вложений быстрым способом
                    has_attachments = False
                    try:
                        # Получаем структуру письма для проверки вложений
                        status_struct, struct_data = self.connection.fetch(msg_id, '(BODYSTRUCTURE)')
                        if status_struct == 'OK':
                            struct_str = str(struct_data[0])
                            # Ищем признаки вложений в структуре
                            has_attachments = 'attachment' in struct_str.lower() or 'name=' in struct_str.lower()
                    except:
                        pass
                    
                    result.append({
                        'id': msg_id.decode(),
                        'message_id': email_message.get('Message-ID', ''),
                        'subject': subject,
                        'from': from_addr,
                        'to': to_addr,
                        'date': date,
                        'is_read': is_read,
                        'is_flagged': is_flagged,
                        'has_attachments': has_attachments
                    })
                except Exception as e:
                    logger.error(f"Error processing message {msg_id}: {str(e)}")
                    continue
            self.disconnect()
            return result
        except Exception as e:
            logger.error(f"Error getting messages: {str(e)}")
            self.disconnect()
            return []

    def get_message_body(self, folder: str, msg_id: str) -> Dict:
        """Получить полное содержимое письма"""
        try:
            self.connect()
            status, data = self.connection.select(f'"{folder}"', readonly=True)
            if status != 'OK':
                self.disconnect()
                return {"error": "Failed to select folder"}
            status, msg_data = self.connection.fetch(msg_id.encode(), '(RFC822)')
            if status != 'OK':
                self.disconnect()
                return {"error": "Failed to fetch message"}
            raw_email = msg_data[0][1]
            email_message = email.message_from_bytes(raw_email)
            subject = self._decode_header(email_message.get('Subject', ''))
            from_addr = self._decode_header(email_message.get('From', ''))
            to_addr = self._decode_header(email_message.get('To', ''))
            cc_addr = self._decode_header(email_message.get('Cc', ''))
            date = email_message.get('Date', '')
            message_id = email_message.get('Message-ID', '')
            in_reply_to = email_message.get('In-Reply-To', '')
            body_text = ""
            body_html = ""
            attachments = []
            inline_images = []
            if email_message.is_multipart():
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get('Content-Disposition', ''))
                    content_id = part.get('Content-ID', '')
                    if content_id and content_type.startswith('image/'):
                        cid = content_id.strip('<>')
                        payload = part.get_payload(decode=True)
                        if payload:
                            # Получаем и декодируем имя файла
                            raw_filename = part.get_filename()
                            if raw_filename:
                                filename = self._decode_header(raw_filename)
                            else:
                                # Определяем расширение по content_type
                                ext = 'jpg'
                                if 'png' in content_type:
                                    ext = 'png'
                                elif 'gif' in content_type:
                                    ext = 'gif'
                                elif 'webp' in content_type:
                                    ext = 'webp'
                                filename = f'inline_{cid}.{ext}'
                            
                            inline_images.append({
                                'cid': cid,
                                'content': payload,
                                'content_type': content_type,
                                'filename': filename
                            })
                        continue
                    if 'attachment' in content_disposition:
                        filename = part.get_filename()
                        if filename:
                            attachments.append({
                                'filename': self._decode_header(filename),
                                'content_type': content_type,
                                'size': len(part.get_payload(decode=True) or b'')
                            })
                    elif content_type == 'text/plain' and not body_text:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body_text = payload.decode('utf-8', errors='ignore')
                    elif content_type == 'text/html' and not body_html:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body_html = payload.decode('utf-8', errors='ignore')
            else:
                payload = email_message.get_payload(decode=True)
                if payload:
                    content_type = email_message.get_content_type()
                    if content_type == 'text/html':
                        body_html = payload.decode('utf-8', errors='ignore')
                    else:
                        body_text = payload.decode('utf-8', errors='ignore')
            self.disconnect()
            return {
                'id': msg_id,
                'message_id': message_id,
                'in_reply_to': in_reply_to,
                'subject': subject,
                'from': from_addr,
                'to': to_addr,
                'cc': cc_addr,
                'date': date,
                'body_text': body_text,
                'body_html': body_html,
                'attachments': attachments,
                'inline_images': inline_images
            }
        except Exception as e:
            logger.error(f"Error getting message body: {str(e)}")
            self.disconnect()
            return {"error": str(e)}

    def mark_as_read(self, folder: str, msg_id: str) -> bool:
        """Пометить письмо как прочитанное"""
        try:
            self.connect()
            status, data = self.connection.select(f'"{folder}"')
            if status != 'OK':
                self.disconnect()
                return False
            self.connection.store(msg_id.encode(), '+FLAGS', '\\Seen')
            self.disconnect()
            return True
        except Exception as e:
            logger.error(f"Error marking as read: {str(e)}")
            self.disconnect()
            return False

    def _decode_header(self, header: str) -> str:
        """Декодирование заголовка письма"""
        if not header:
            return ""
        decoded_parts = []
        for part, encoding in decode_header(header):
            if isinstance(part, bytes):
                try:
                    if encoding:
                        decoded_parts.append(part.decode(encoding))
                    else:
                        decoded_parts.append(part.decode('utf-8', errors='ignore'))
                except:
                    decoded_parts.append(part.decode('utf-8', errors='ignore'))
            else:
                decoded_parts.append(str(part))
        return ' '.join(decoded_parts)

    def get_attachment(self, folder: str, msg_id: str, attachment_index: int) -> Optional[Dict]:
        """Получить конкретное вложение из письма"""
        try:
            self.connect()
            status, data = self.connection.select(f'"{folder}"', readonly=True)
            if status != 'OK':
                self.disconnect()
                return None
            status, msg_data = self.connection.fetch(msg_id.encode(), '(RFC822)')
            if status != 'OK':
                self.disconnect()
                return None
            raw_email = msg_data[0][1]
            email_message = email.message_from_bytes(raw_email)
            current_index = 0
            if email_message.is_multipart():
                for part in email_message.walk():
                    content_disposition = str(part.get('Content-Disposition', ''))
                    if 'attachment' in content_disposition:
                        if current_index == attachment_index:
                            filename = part.get_filename()
                            content = part.get_payload(decode=True)
                            content_type = part.get_content_type()
                            self.disconnect()
                            return {
                                'filename': self._decode_header(filename) if filename else 'attachment',
                                'content': content,
                                'content_type': content_type
                            }
                        current_index += 1
            self.disconnect()
            return None
        except Exception as e:
            logger.error(f"Error getting attachment: {str(e)}")
            self.disconnect()
            return None
