from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.config import settings
from app.schemas.price_request import PriceRequestCreate, PriceRequestResponse
from app.tasks.email_tasks import send_price_request_email
from app.models.supplier import Supplier
from sqlalchemy import select
from uuid import UUID

router = APIRouter()

@router.get("/defaults")
async def get_price_request_defaults():
    """Возвращает шаблон письма для фронтенда"""
    return {
        "subject": settings.PRICE_REQUEST_DEFAULT_SUBJECT,
        "body": settings.PRICE_REQUEST_DEFAULT_HEADER.replace('\\n', '\n'),
        "reply_to": settings.PRICE_REQUEST_REPLY_TO_EMAIL
    }

@router.post("/send", response_model=PriceRequestResponse)
async def send_price_requests(request: PriceRequestCreate, db: AsyncSession = Depends(get_db)):
    """Отправить запрос цен поставщикам"""
    results = []
    sent_count = 0
    failed_count = 0
    
    supplier_uuids = [UUID(sid) for sid in request.supplier_ids]
    result = await db.execute(select(Supplier).where(Supplier.id.in_(supplier_uuids)))
    suppliers = result.scalars().all()
    
    # Формируем список товаров
    products_text = "\n".join([
        f"- {p.name}" + (f" (Артикул: {p.sku})" if p.sku else "")
        for p in request.products
    ])
    
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
            # Собираем письмо из трех частей ENV
            header = settings.PRICE_REQUEST_DEFAULT_HEADER.replace('\\n', '\n')
            footer = settings.PRICE_REQUEST_DEFAULT_FOOTER.replace('\\n', '\n')
            email_body = f"{header}\n\n{products_text}{footer}"
            
            task = send_price_request_email.delay(
                supplier_email=supplier.email,
                supplier_name=supplier.name,
                subject=request.subject,
                body=email_body
            )
            
            sent_count += 1
            results.append({
                "supplier_id": str(supplier.id),
                "supplier_name": supplier.name,
                "supplier_email": supplier.email,
                "success": True,
                "task_id": task.id
            })
            
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
