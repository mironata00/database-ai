from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.models.email_provider import EmailProvider
from app.schemas.email_provider import (
    EmailProviderCreate,
    EmailProviderUpdate,
    EmailProviderResponse,
    EmailProviderShort
)
from app.api.auth import get_current_user

router = APIRouter()


def require_admin(current_user: dict = Depends(get_current_user)):
    """Проверка что пользователь - администратор"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ только для администраторов"
        )
    return current_user


@router.get("/", response_model=List[EmailProviderResponse])
async def list_providers(
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить список всех провайдеров почты"""
    query = select(EmailProvider)
    if active_only:
        query = query.where(EmailProvider.is_active == True)
    query = query.order_by(EmailProvider.display_name)
    
    result = await db.execute(query)
    providers = result.scalars().all()
    
    return [
        EmailProviderResponse(
            id=str(provider.id),
            name=provider.name,
            display_name=provider.display_name,
            imap_host=provider.imap_host,
            imap_port=provider.imap_port,
            imap_use_ssl=provider.imap_use_ssl,
            smtp_host=provider.smtp_host,
            smtp_port=provider.smtp_port,
            smtp_use_tls=provider.smtp_use_tls,
            description=provider.description,
            is_active=provider.is_active,
            created_at=provider.created_at,
            updated_at=provider.updated_at
        )
        for provider in providers
    ]


@router.get("/short", response_model=List[EmailProviderShort])
async def list_providers_short(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Краткий список провайдеров для выпадающего меню"""
    result = await db.execute(
        select(EmailProvider)
        .where(EmailProvider.is_active == True)
        .order_by(EmailProvider.display_name)
    )
    providers = result.scalars().all()
    
    return [
        EmailProviderShort(
            id=str(provider.id),
            name=provider.name,
            display_name=provider.display_name,
            imap_host=provider.imap_host,
            imap_port=provider.imap_port,
            imap_use_ssl=provider.imap_use_ssl,
            smtp_host=provider.smtp_host,
            smtp_port=provider.smtp_port,
            smtp_use_tls=provider.smtp_use_tls
        )
        for provider in providers
    ]


@router.get("/{provider_id}", response_model=EmailProviderResponse)
async def get_provider(
    provider_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Получить провайдера по ID"""
    result = await db.execute(
        select(EmailProvider).where(EmailProvider.id == provider_id)
    )
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Провайдер не найден"
        )
    
    return EmailProviderResponse(
        id=str(provider.id),
        name=provider.name,
        display_name=provider.display_name,
        imap_host=provider.imap_host,
        imap_port=provider.imap_port,
        imap_use_ssl=provider.imap_use_ssl,
        smtp_host=provider.smtp_host,
        smtp_port=provider.smtp_port,
        smtp_use_tls=provider.smtp_use_tls,
        description=provider.description,
        is_active=provider.is_active,
        created_at=provider.created_at,
        updated_at=provider.updated_at
    )


@router.post("/", response_model=EmailProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_provider(
    data: EmailProviderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Создать нового провайдера почты"""
    # Проверяем уникальность имени
    existing = await db.execute(
        select(EmailProvider).where(EmailProvider.name == data.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Провайдер с именем '{data.name}' уже существует"
        )
    
    provider = EmailProvider(
        name=data.name,
        display_name=data.display_name,
        imap_host=data.imap_host,
        imap_port=data.imap_port,
        imap_use_ssl=data.imap_use_ssl,
        smtp_host=data.smtp_host,
        smtp_port=data.smtp_port,
        smtp_use_tls=data.smtp_use_tls,
        description=data.description,
        is_active=data.is_active
    )
    
    db.add(provider)
    await db.commit()
    await db.refresh(provider)
    
    return EmailProviderResponse(
        id=str(provider.id),
        name=provider.name,
        display_name=provider.display_name,
        imap_host=provider.imap_host,
        imap_port=provider.imap_port,
        imap_use_ssl=provider.imap_use_ssl,
        smtp_host=provider.smtp_host,
        smtp_port=provider.smtp_port,
        smtp_use_tls=provider.smtp_use_tls,
        description=provider.description,
        is_active=provider.is_active,
        created_at=provider.created_at,
        updated_at=provider.updated_at
    )


@router.put("/{provider_id}", response_model=EmailProviderResponse)
async def update_provider(
    provider_id: str,
    data: EmailProviderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Обновить провайдера почты"""
    result = await db.execute(
        select(EmailProvider).where(EmailProvider.id == provider_id)
    )
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Провайдер не найден"
        )
    
    # Проверяем уникальность имени если меняется
    if data.name and data.name != provider.name:
        existing = await db.execute(
            select(EmailProvider).where(EmailProvider.name == data.name)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Провайдер с именем '{data.name}' уже существует"
            )
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(provider, field, value)
    
    await db.commit()
    await db.refresh(provider)
    
    return EmailProviderResponse(
        id=str(provider.id),
        name=provider.name,
        display_name=provider.display_name,
        imap_host=provider.imap_host,
        imap_port=provider.imap_port,
        imap_use_ssl=provider.imap_use_ssl,
        smtp_host=provider.smtp_host,
        smtp_port=provider.smtp_port,
        smtp_use_tls=provider.smtp_use_tls,
        description=provider.description,
        is_active=provider.is_active,
        created_at=provider.created_at,
        updated_at=provider.updated_at
    )


@router.delete("/{provider_id}")
async def delete_provider(
    provider_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Удалить провайдера почты"""
    result = await db.execute(
        select(EmailProvider).where(EmailProvider.id == provider_id)
    )
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Провайдер не найден"
        )
    
    # Проверяем что провайдер не используется
    if provider.name == "custom":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить системного провайдера 'custom'"
        )
    
    await db.delete(provider)
    await db.commit()
    
    return {"success": True, "message": "Провайдер удален"}
