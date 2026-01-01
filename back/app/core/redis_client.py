import redis
from app.core.config import settings

# Создаем подключение к Redis с паролем
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,  # Добавлен пароль!
    db=0,
    decode_responses=True
)
