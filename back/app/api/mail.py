from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.core.database import get_db
from app.models.user import User
from app.api.auth import get_current_user
from app.utils.imap_client import IMAPClientPersonal
from app.utils.email_sender_personal import send_email_from_user
from app.utils.encryption import encryption
from pydantic import BaseModel

router = APIRouter()


class SendEmailRequest(BaseModel):
    to: str
    subject: str
    body: str
    reply_to: Optional[str] = None


class MarkReadRequest(BaseModel):
    folder: str = "INBOX"


@router.get("/config")
async def get_mail_config(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Проверка настроек почты текущего пользователя"""
    result = await db.execute(
        select(User).where(User.id == current_user.get("id"))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return {
        "has_smtp_configured": user.has_smtp_configured(),
        "has_imap_configured": user.has_imap_configured(),
        "has_email_configured": user.has_email_configured(),
        "smtp_user": user.smtp_user,
        "imap_user": user.imap_user
    }


@router.get("/folders")
async def get_folders(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить список папок почты"""
    result = await db.execute(
        select(User).where(User.id == current_user.get("id"))
    )
    user = result.scalar_one_or_none()

    if not user or not user.has_imap_configured():
        raise HTTPException(status_code=400, detail="IMAP не настроен")

    try:
        client = IMAPClientPersonal(
            host=user.imap_host,
            port=user.imap_port,
            user=user.imap_user,
            password=user.imap_password,
            use_ssl=user.imap_use_ssl
        )
        folders = client.get_folders()
        return {"folders": folders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка подключения к IMAP: {str(e)}")


@router.get("/messages")
async def get_messages(
    folder: str = Query("INBOX"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    unread_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить список писем"""
    result = await db.execute(
        select(User).where(User.id == current_user.get("id"))
    )
    user = result.scalar_one_or_none()

    if not user or not user.has_imap_configured():
        raise HTTPException(status_code=400, detail="IMAP не настроен")

    try:
        client = IMAPClientPersonal(
            host=user.imap_host,
            port=user.imap_port,
            user=user.imap_user,
            password=user.imap_password,
            use_ssl=user.imap_use_ssl
        )
        messages = client.get_messages(
            folder=folder,
            limit=limit,
            offset=offset,
            unread_only=unread_only
        )
        return {"messages": messages, "total": len(messages)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения писем: {str(e)}")


@router.get("/messages/{msg_id}")
async def get_message(
    msg_id: str,
    folder: str = Query("INBOX"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить содержимое письма"""
    result = await db.execute(
        select(User).where(User.id == current_user.get("id"))
    )
    user = result.scalar_one_or_none()

    if not user or not user.has_imap_configured():
        raise HTTPException(status_code=400, detail="IMAP не настроен")

    try:
        client = IMAPClientPersonal(
            host=user.imap_host,
            port=user.imap_port,
            user=user.imap_user,
            password=user.imap_password,
            use_ssl=user.imap_use_ssl
        )
        message = client.get_message_body(folder=folder, msg_id=msg_id)

        if "error" in message:
            raise HTTPException(status_code=404, detail=message["error"])

        return message
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения письма: {str(e)}")


@router.post("/messages/{msg_id}/read")
async def mark_as_read(
    msg_id: str,
    data: MarkReadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Пометить письмо как прочитанное"""
    result = await db.execute(
        select(User).where(User.id == current_user.get("id"))
    )
    user = result.scalar_one_or_none()

    if not user or not user.has_imap_configured():
        raise HTTPException(status_code=400, detail="IMAP не настроен")

    try:
        client = IMAPClientPersonal(
            host=user.imap_host,
            port=user.imap_port,
            user=user.imap_user,
            password=user.imap_password,
            use_ssl=user.imap_use_ssl
        )
        success = client.mark_as_read(folder=data.folder, msg_id=msg_id)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@router.post("/send")
async def send_email(
    data: SendEmailRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Отправить письмо и сохранить в папку Отправленные"""
    result = await db.execute(
        select(User).where(User.id == current_user.get("id"))
    )
    user = result.scalar_one_or_none()

    if not user or not user.has_smtp_configured():
        raise HTTPException(status_code=400, detail="SMTP не настроен")

    try:
        smtp_config = {
            'host': user.smtp_host,
            'port': user.smtp_port,
            'user': user.smtp_user,
            'password': user.smtp_password,
            'use_tls': user.smtp_use_tls,
            'from_name': user.smtp_from_name or user.full_name or user.smtp_user,
            'from_email': user.smtp_user
        }

        # IMAP конфиг для сохранения в "Отправленные"
        imap_config = None
        if user.has_imap_configured():
            imap_config = {
                'host': user.imap_host,
                'port': user.imap_port,
                'user': user.imap_user,
                'password': user.imap_password,
                'use_ssl': user.imap_use_ssl
            }

        result = send_email_from_user(
            user_smtp_config=smtp_config,
            to_email=data.to,
            subject=data.subject,
            body=data.body,
            reply_to=data.reply_to,
            save_to_sent=True,
            imap_config=imap_config
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка отправки: {str(e)}")
