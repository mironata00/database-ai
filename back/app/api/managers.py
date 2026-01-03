from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import logging

from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.email_provider import EmailProvider
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.core.security import security
from app.api.auth import get_current_user
from app.utils.encryption import encryption

router = APIRouter()
logger = logging.getLogger(__name__)


def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ только для администраторов"
        )
    return current_user


def user_to_response(user: User) -> UserResponse:
    """Конвертация модели User в UserResponse"""
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        email_provider_id=str(user.email_provider_id) if user.email_provider_id else None,
        has_smtp_configured=user.has_smtp_configured(),
        has_imap_configured=user.has_imap_configured(),
        has_email_configured=user.has_email_configured(),
        smtp_host=user.smtp_host,
        smtp_port=user.smtp_port,
        smtp_user=user.smtp_user,
        smtp_from_name=user.smtp_from_name,
        smtp_use_tls=user.smtp_use_tls,
        imap_host=user.imap_host,
        imap_port=user.imap_port,
        imap_user=user.imap_user,
        imap_use_ssl=user.imap_use_ssl,
        email_default_subject=user.email_default_subject,
        email_default_body=user.email_default_body,
        email_signature=user.email_signature
    )


@router.post("/", response_model=UserResponse)
async def create_manager(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Создать нового менеджера"""
    logger.info(f"Creating manager with data: {user_data.model_dump(exclude={'password', 'smtp_password', 'imap_password'})}")
    
    # Проверяем уникальность email
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email уже зарегистрирован"
        )
    
    # Проверяем существование провайдера если указан
    provider_id = None
    if user_data.email_provider_id:
        provider_result = await db.execute(
            select(EmailProvider).where(EmailProvider.id == user_data.email_provider_id)
        )
        if not provider_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Провайдер почты не найден"
            )
        provider_id = user_data.email_provider_id
    
    # Шифруем пароли перед сохранением
    smtp_password_encrypted = encryption.encrypt(user_data.smtp_password) if user_data.smtp_password else None
    imap_password_encrypted = encryption.encrypt(user_data.imap_password) if user_data.imap_password else None
    
    new_user = User(
        email=user_data.email,
        hashed_password=security.get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        is_active=True,
        email_provider_id=provider_id,
        # SMTP
        smtp_host=user_data.smtp_host,
        smtp_port=user_data.smtp_port or 587,
        smtp_user=user_data.smtp_user,
        smtp_password=smtp_password_encrypted,
        smtp_use_tls=user_data.smtp_use_tls if user_data.smtp_use_tls is not None else True,
        smtp_from_name=user_data.smtp_from_name,
        # IMAP
        imap_host=user_data.imap_host,
        imap_port=user_data.imap_port or 993,
        imap_user=user_data.imap_user,
        imap_password=imap_password_encrypted,
        imap_use_ssl=user_data.imap_use_ssl if user_data.imap_use_ssl is not None else True,
        # Email шаблоны
        email_default_subject=user_data.email_default_subject or "Запрос цен",
        email_default_body=user_data.email_default_body or "Добрый день!\n\nПросим предоставить актуальные цены и сроки поставки на следующие товары:",
        email_signature=user_data.email_signature or "С уважением,"
    )
    
    logger.info(f"New user IMAP config: host={new_user.imap_host}, user={new_user.imap_user}")
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return user_to_response(new_user)


@router.get("/", response_model=List[UserResponse])
async def list_managers(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Получить список всех менеджеров и админов"""
    result = await db.execute(
        select(User)
        .where(User.role.in_([UserRole.manager, UserRole.admin, UserRole.viewer]))
        .order_by(User.created_at.desc())
        .limit(limit)
    )
    users = result.scalars().all()
    
    return [user_to_response(user) for user in users]


@router.get("/{user_id}", response_model=UserResponse)
async def get_manager(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Получить менеджера по ID"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    return user_to_response(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_manager_patch(
    user_id: str,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Частичное обновление менеджера (PATCH)"""
    return await _update_manager(user_id, user_data, db)


@router.put("/{user_id}", response_model=UserResponse)
async def update_manager_put(
    user_id: str,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Полное обновление менеджера (PUT)"""
    return await _update_manager(user_id, user_data, db)


async def _update_manager(user_id: str, user_data: UserUpdate, db: AsyncSession) -> UserResponse:
    """Внутренняя функция обновления менеджера"""
    logger.info(f"Updating manager {user_id} with data: {user_data.model_dump(exclude={'password', 'smtp_password', 'imap_password'})}")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    update_data = user_data.model_dump(exclude_unset=True)
    logger.info(f"Update data after model_dump: {list(update_data.keys())}")
    
    # Хешируем пароль пользователя если передан
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = security.get_password_hash(update_data.pop("password"))
    elif "password" in update_data:
        del update_data["password"]
    
    # Шифруем SMTP пароль если передан
    if "smtp_password" in update_data and update_data["smtp_password"]:
        update_data["smtp_password"] = encryption.encrypt(update_data["smtp_password"])
    elif "smtp_password" in update_data and not update_data["smtp_password"]:
        # Если пустой - не обновляем (оставляем старый)
        del update_data["smtp_password"]
    
    # Шифруем IMAP пароль если передан
    if "imap_password" in update_data and update_data["imap_password"]:
        update_data["imap_password"] = encryption.encrypt(update_data["imap_password"])
    elif "imap_password" in update_data and not update_data["imap_password"]:
        # Если пустой - не обновляем (оставляем старый)
        del update_data["imap_password"]
    
    # Проверяем провайдера если меняется
    if "email_provider_id" in update_data and update_data["email_provider_id"]:
        provider_result = await db.execute(
            select(EmailProvider).where(EmailProvider.id == update_data["email_provider_id"])
        )
        if not provider_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Провайдер почты не найден"
            )
    
    logger.info(f"Final update fields: {list(update_data.keys())}")
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    logger.info(f"Updated user IMAP config: host={user.imap_host}, user={user.imap_user}")
    
    return user_to_response(user)


@router.delete("/{user_id}")
async def delete_manager(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Удалить менеджера"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Нельзя удалить самого себя
    if str(user.id) == current_user.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить свой аккаунт"
        )
    
    await db.delete(user)
    await db.commit()
    
    return {"success": True, "message": "Пользователь удален"}
