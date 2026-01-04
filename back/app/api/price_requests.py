from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.core.database import get_db
from app.schemas.price_request import PriceRequestCreate, PriceRequestResponse
from app.tasks.email_tasks import send_price_request_email_personal
from app.models.supplier import Supplier
from app.models.user import User
from app.api.auth import get_current_user
import time

router = APIRouter()

@router.get("/defaults")
async def get_price_request_defaults(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Возвращает шаблон письма для текущего менеджера"""
    result = await db.execute(select(User).where(User.id == current_user['id']))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "subject": user.email_default_subject or "Запрос цен",
        "body": user.email_default_body or "Добрый день!\n\nПросим предоставить актуальные цены и сроки поставки на следующие товары:",
        "signature": user.email_signature or "С уважением,",
        "from_name": user.smtp_from_name or user.full_name or "Database AI",
        "from_email": user.smtp_user or user.email,
        "has_smtp": user.has_smtp_configured()
    }

@router.post("/send", response_model=PriceRequestResponse)
async def send_price_requests(
    request: PriceRequestCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Отправить запрос цен от имени текущего менеджера"""
    
    # Получаем полные данные user с SMTP
    result = await db.execute(select(User).where(User.id == current_user['id']))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.has_smtp_configured():
        raise HTTPException(
            status_code=400,
            detail="SMTP не настроен. Обратитесь к администратору для настройки отправки писем."
        )
    
    # Формируем SMTP конфиг менеджера
    user_smtp_config = {
        'host': user.smtp_host,
        'port': user.smtp_port,
        'user': user.smtp_user,
        'password': user.smtp_password,
        'use_tls': user.smtp_use_tls,
        'from_name': user.smtp_from_name or user.full_name or "Database AI",
        'from_email': user.smtp_user
    }

    # Формируем IMAP конфиг для сохранения в Отправленные
    user_imap_config = None
    if user.has_imap_configured():
        user_imap_config = {
            'host': user.imap_host,
            'port': user.imap_port,
            'user': user.imap_user,
            'password': user.imap_password,
            'use_ssl': user.imap_use_ssl
        }
    
    results = []
    sent_count = 0
    failed_count = 0
    
    # Получаем поставщиков
    supplier_uuids = [UUID(sid) for sid in request.supplier_ids]
    result = await db.execute(select(Supplier).where(Supplier.id.in_(supplier_uuids)))
    suppliers = result.scalars().all()
    
    # Формируем список товаров
    products_text = "\n".join([
        f"- {p.name}" + (f" (Артикул: {p.sku})" if p.sku else "")
        for p in request.products
    ])
    
    # Добавляем подпись менеджера
    signature = user.email_signature or ""
    email_body = f"{request.body}\n\n{products_text}\n{signature}"
    
    # Отправляем письма с паузой 3 сек
    for supplier in suppliers:
        if not supplier.email:
            failed_count += 1
            results.append({
                "supplier_id": str(supplier.id),
                "supplier_name": supplier.name,
                "success": False,
                "error": "No email address"
            })
            continue
        
        try:
            # Отправляем через Celery task (с сохранением в Отправленные)
            task = send_price_request_email_personal.delay(
                user_smtp_config=user_smtp_config,
                to_email=supplier.email,
                subject=request.subject,
                body=email_body,
                reply_to=user.email,
                imap_config=user_imap_config
            )
            
            sent_count += 1
            results.append({
                "supplier_id": str(supplier.id),
                "supplier_name": supplier.name,
                "supplier_email": supplier.email,
                "success": True,
                "task_id": task.id,
                "from_email": user_smtp_config['from_email']
            })
            
            # Пауза 3 секунды между отправками
            time.sleep(3)
            
        except Exception as e:
            failed_count += 1
            results.append({
                "supplier_id": str(supplier.id),
                "supplier_name": supplier.name,
                "success": False,
                "error": str(e)
            })
    
    return PriceRequestResponse(
        success=sent_count > 0,
        sent_count=sent_count,
        failed_count=failed_count,
        details=results
    )
