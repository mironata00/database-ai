from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from app.models.audit_log import AuditLog, AuditAction
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from jose import jwt, JWTError
import logging

logger = logging.getLogger(__name__)

# Создаем синхронную сессию для middleware
sync_engine = create_engine(
    settings.DATABASE_URL.replace('postgresql+asyncpg', 'postgresql+psycopg2'),
    pool_pre_ping=True
)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

class AuditMiddleware(BaseHTTPMiddleware):
    def extract_user_id(self, request: Request):
        """Извлекает user_id из JWT токена"""
        try:
            auth_header = request.headers.get('authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.replace('Bearer ', '')
                payload = jwt.decode(
                    token, 
                    settings.JWT_SECRET_KEY,  # Используем JWT_SECRET_KEY
                    algorithms=[settings.JWT_ALGORITHM]  # Используем JWT_ALGORITHM
                )
                user_id = payload.get('sub')
                logger.debug(f"Extracted user_id from token: {user_id}")
                return user_id
        except JWTError as e:
            logger.debug(f"JWT decode error: {e}")
        except Exception as e:
            logger.debug(f"Could not extract user_id: {e}")
        return None
    
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
                
                # Получаем user_id из JWT токена
                user_id = self.extract_user_id(request)
                
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
                    logger.info(f"Audit log created: {action_map.get(request.method)} {entity_type} by user {user_id}")
                except Exception as e:
                    logger.error(f"Failed to create audit log: {e}")
                    db.rollback()
                finally:
                    db.close()
                    
            except Exception as e:
                logger.error(f"Audit middleware error: {e}")
        
        return response
