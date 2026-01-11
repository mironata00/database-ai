"""
MinIO Client для хранения файлов (вложений почты, прайс-листов и т.д.)
"""
from minio import Minio
from minio.error import S3Error
import logging
import io
from typing import Optional
import os

logger = logging.getLogger(__name__)


class MinIOClient:
    def __init__(self):
        self.endpoint = os.getenv('MINIO_ENDPOINT', 'minio:9000')
        self.access_key = os.getenv('MINIO_ROOT_USER', 'minioadmin')
        self.secret_key = os.getenv('MINIO_ROOT_PASSWORD', 'minioadmin')
        self.secure = os.getenv('MINIO_SECURE', 'false').lower() == 'true'
        
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )
        
        # Создаем бакеты если их нет
        self._ensure_buckets()
    
    def _ensure_buckets(self):
        """Создать необходимые бакеты"""
        buckets = ['email-attachments', 'pricelists', 'documents']
        
        for bucket in buckets:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    logger.info(f"Created MinIO bucket: {bucket}")
            except S3Error as e:
                logger.error(f"Error creating bucket {bucket}: {e}")
    
    def upload_file(self, bucket: str, object_name: str, data: bytes, content_type: str = 'application/octet-stream') -> bool:
        """
        Загрузить файл в MinIO
        
        Args:
            bucket: Название бакета
            object_name: Имя объекта (путь к файлу)
            data: Байты файла
            content_type: MIME тип
        
        Returns:
            True если успешно
        """
        try:
            data_stream = io.BytesIO(data)
            self.client.put_object(
                bucket,
                object_name,
                data_stream,
                length=len(data),
                content_type=content_type
            )
            logger.info(f"Uploaded file to MinIO: {bucket}/{object_name}")
            return True
        except S3Error as e:
            logger.error(f"Error uploading to MinIO: {e}")
            return False
    
    def download_file(self, bucket: str, object_name: str) -> Optional[bytes]:
        """
        Скачать файл из MinIO
        
        Args:
            bucket: Название бакета
            object_name: Имя объекта
        
        Returns:
            Байты файла или None
        """
        try:
            response = self.client.get_object(bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            logger.error(f"Error downloading from MinIO: {e}")
            return None

    def get_file(self, bucket: str, object_name: str) -> Optional[bytes]:
        """
        Получить файл из MinIO (alias для download_file)
        Args:
            bucket: Название бакета
            object_name: Имя объекта
        Returns:
            Байты файла или None
        """
        return self.download_file(bucket, object_name)
    
    def get_file_url(self, bucket: str, object_name: str, expires: int = 3600) -> Optional[str]:
        """
        Получить временную ссылку на файл
        
        Args:
            bucket: Название бакета
            object_name: Имя объекта
            expires: Время жизни ссылки в секундах (по умолчанию 1 час)
        
        Returns:
            URL или None
        """
        try:
            url = self.client.presigned_get_object(bucket, object_name, expires=expires)
            return url
        except S3Error as e:
            logger.error(f"Error generating URL: {e}")
            return None
    
    def delete_file(self, bucket: str, object_name: str) -> bool:
        """
        Удалить файл из MinIO
        
        Args:
            bucket: Название бакета
            object_name: Имя объекта
        
        Returns:
            True если успешно
        """
        try:
            self.client.remove_object(bucket, object_name)
            logger.info(f"Deleted file from MinIO: {bucket}/{object_name}")
            return True
        except S3Error as e:
            logger.error(f"Error deleting from MinIO: {e}")
            return False
    
    def file_exists(self, bucket: str, object_name: str) -> bool:
        """
        Проверить существование файла
        
        Args:
            bucket: Название бакета
            object_name: Имя объекта
        
        Returns:
            True если файл существует
        """
        try:
            self.client.stat_object(bucket, object_name)
            return True
        except S3Error:
            return False


# Глобальный экземпляр клиента
minio_client = MinIOClient()
