from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.user import User
from app.api.auth import get_current_user
from app.tasks.auto_supplier_tasks import process_supplier_emails
from app.models.supplier import Supplier
import logging

router = APIRouter(prefix="/auto-suppliers", tags=["Auto Suppliers"])
logger = logging.getLogger(__name__)

@router.post("/process-emails")
async def trigger_email_processing(
    current_user: User = Depends(get_current_user)
):
    """
    Ручной запуск обработки писем с прайс-листами
    Только для админов
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Запускаем задачу асинхронно
    task = process_supplier_emails.delay()
    
    return {
        "message": "Email processing started",
        "task_id": task.id
    }

@router.get("/pending-suppliers")
async def get_pending_suppliers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить список поставщиков на модерации (созданных автоматически)
    """
    result = await db.execute(
        select(Supplier).where(Supplier.status == "PENDING").order_by(Supplier.created_at.desc())
    )
    suppliers = result.scalars().all()
    
    return {
        "count": len(suppliers),
        "suppliers": [
            {
                "id": str(s.id),
                "name": s.name,
                "inn": s.inn,
                "email": s.email,
                "phone": s.phone,
                "tags": s.tags_array,
                "created_at": s.created_at.isoformat(),
            }
            for s in suppliers
        ]
    }

@router.post("/approve/{supplier_id}")
async def approve_supplier(
    supplier_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Одобрить поставщика (изменить статус с PENDING на ACTIVE)
    Только для админов
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    supplier.status = "ACTIVE"
    await db.commit()
    await db.refresh(supplier)
    
    return {
        "message": "Supplier approved",
        "supplier": {
            "id": str(supplier.id),
            "name": supplier.name,
            "status": supplier.status
        }
    }
