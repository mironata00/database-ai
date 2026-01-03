"""
Утилита для шифрования/дешифрования чувствительных данных.
Использует Fernet (AES-128-CBC с HMAC).
"""
from cryptography.fernet import Fernet
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class EncryptionManager:
    """Менеджер шифрования для паролей и других чувствительных данных"""
    
    def __init__(self):
        self._fernet = None
        self._init_fernet()
    
    def _init_fernet(self):
        """Инициализация Fernet с ключом из настроек"""
        try:
            key = settings.ENCRYPTION_KEY
            if not key:
                logger.warning("ENCRYPTION_KEY not set! Encryption disabled.")
                return
            
            # Fernet требует base64-encoded 32-byte key
            self._fernet = Fernet(key.encode() if isinstance(key, str) else key)
            logger.info("Encryption initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            self._fernet = None
    
    def encrypt(self, plain_text: str) -> str:
        """
        Шифрует строку.
        Возвращает зашифрованную строку с префиксом 'enc:' для идентификации.
        """
        if not plain_text:
            return plain_text
        
        if not self._fernet:
            logger.warning("Encryption not available, storing plain text")
            return plain_text
        
        # Если уже зашифровано - возвращаем как есть
        if plain_text.startswith('enc:'):
            return plain_text
        
        try:
            encrypted = self._fernet.encrypt(plain_text.encode('utf-8'))
            return f"enc:{encrypted.decode('utf-8')}"
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return plain_text
    
    def decrypt(self, encrypted_text: str) -> str:
        """
        Дешифрует строку.
        Если строка не зашифрована (нет префикса 'enc:'), возвращает как есть.
        """
        if not encrypted_text:
            return encrypted_text
        
        # Если не зашифровано - возвращаем как есть (для обратной совместимости)
        if not encrypted_text.startswith('enc:'):
            return encrypted_text
        
        if not self._fernet:
            logger.warning("Decryption not available")
            return encrypted_text
        
        try:
            # Убираем префикс 'enc:'
            encrypted_data = encrypted_text[4:]
            decrypted = self._fernet.decrypt(encrypted_data.encode('utf-8'))
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return encrypted_text
    
    def is_encrypted(self, text: str) -> bool:
        """Проверяет, зашифрована ли строка"""
        return text.startswith('enc:') if text else False


# Singleton instance
encryption = EncryptionManager()
