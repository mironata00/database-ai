from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import io
import uuid
from datetime import datetime

from app.core.database import get_db
from app.models.user import User
from app.api.auth import get_current_user
from app.utils.imap_client import IMAPClientPersonal
from app.utils.email_sender_personal import send_email_from_user_with_attachments
from app.utils.encryption import encryption
from app.utils.minio_client import minio_client
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
    """Получить содержимое письма с сохранением вложений в MinIO"""
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

        # Сохраняем вложения в MinIO и заменяем на ссылки
        if message.get('attachments'):
            for idx, attachment in enumerate(message['attachments']):
                # Генерируем уникальное имя файла
                file_id = str(uuid.uuid4())
                timestamp = datetime.now().strftime('%Y%m%d')
                object_name = f"{timestamp}/{user.id}/{msg_id}/{file_id}_{attachment['filename']}"
                
                # Получаем содержимое вложения
                attachment_data = client.get_attachment(folder=folder, msg_id=msg_id, attachment_index=idx)
                
                if attachment_data and attachment_data.get('content'):
                    # Сохраняем в MinIO
                    success = minio_client.upload_file(
                        bucket='email-attachments',
                        object_name=object_name,
                        data=attachment_data['content'],
                        content_type=attachment.get('content_type', 'application/octet-stream')
                    )
                    
                    if success:
                        # Добавляем информацию для скачивания
                        attachment['minio_path'] = object_name
                        attachment['download_index'] = idx

        return message
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения письма: {str(e)}")


@router.get("/messages/{msg_id}/attachments/{attachment_index}")
async def download_attachment(
    msg_id: str,
    attachment_index: int,
    folder: str = Query("INBOX"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Скачать вложение из письма"""
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
        
        attachment_data = client.get_attachment(
            folder=folder, 
            msg_id=msg_id, 
            attachment_index=attachment_index
        )

        if not attachment_data:
            raise HTTPException(status_code=404, detail="Вложение не найдено")

        return StreamingResponse(
            io.BytesIO(attachment_data['content']),
            media_type=attachment_data['content_type'],
            headers={
                'Content-Disposition': f'attachment; filename="{attachment_data["filename"]}"'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка скачивания вложения: {str(e)}")


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
    to: str = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    reply_to: Optional[str] = Form(None),
    files: List[UploadFile] = File(default=[]),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Отправить письмо с вложениями"""
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

        # Подготовка вложений и сохранение в MinIO
        attachments = []
        minio_paths = []
        
        for file in files:
            content = await file.read()
            
            # Сохраняем в MinIO
            file_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime('%Y%m%d')
            object_name = f"sent/{timestamp}/{user.id}/{file_id}_{file.filename}"
            
            minio_client.upload_file(
                bucket='email-attachments',
                object_name=object_name,
                data=content,
                content_type=file.content_type or 'application/octet-stream'
            )
            
            minio_paths.append({
                'filename': file.filename,
                'minio_path': object_name,
                'size': len(content)
            })
            
            attachments.append({
                'filename': file.filename,
                'content': content,
                'content_type': file.content_type or 'application/octet-stream'
            })

        result = send_email_from_user_with_attachments(
            user_smtp_config=smtp_config,
            to_email=to,
            subject=subject,
            body=body,
            attachments=attachments,
            reply_to=reply_to,
            save_to_sent=True,
            imap_config=imap_config
        )
        
        result['minio_attachments'] = minio_paths

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка отправки: {str(e)}")
