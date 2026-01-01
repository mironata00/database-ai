from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from app.models.audit_log import AuditLog, AuditAction
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Создаем синхронную сессию для middleware
sync_engine = create_engine(
    settings.DATABASE_URL.replace('postgresql+asyncpg', 'postgresql+psycopg2'),
    pool_pre_ping=True
)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Логируем запрос в консоль
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            logger.info(f"Audit: {request.method} {request.url.path} from {request.client.host}")
        
        # Выполняем запрос
        response = await call_next(request)
        
        # Записываем в БД только для модифицирующих операций
        if request.method in ["POST", "PUT", "DELETE", "PATCH"] and response.status_code < 400:
            try:
                # Определяем тип действия
                action_map = {
                    "POST": AuditAction.CREATE,
                    "PUT": AuditAction.UPDATE,
                    "PATCH": AuditAction.UPDATE,
                    "DELETE": AuditAction.DELETE
                }
                
                # Извлекаем entity_type из URL
                path_parts = request.url.path.strip('/').split('/')
                entity_type = path_parts[1] if len(path_parts) > 1 else "unknown"
                entity_id = path_parts[2] if len(path_parts) > 2 else None
                
                # Получаем user_id из токена (если есть)
                user_id = None
                if hasattr(request.state, 'user'):
                    user_id = request.state.user.id
                
                # Создаем запись в БД
                db = SyncSessionLocal()
                try:
                    audit_log = AuditLog(
                        user_id=user_id,
                        action=action_map.get(request.method),
                        entity_type=entity_type,
                        entity_id=entity_id,
                        endpoint=str(request.url.path),
                        ip_address=request.client.host,
                        user_agent=request.headers.get('user-agent', '')[:500]
                    )
                    db.add(audit_log)
                    db.commit()
                except Exception as e:
                    logger.error(f"Failed to create audit log: {e}")
                    db.rollback()
                finally:
                    db.close()
                    
            except Exception as e:
                logger.error(f"Audit middleware error: {e}")
        
        return response
