from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.supplier_request import SupplierRequestCreate, SupplierRequestResponse, SupplierRequestUpdate
from app.models.supplier_request import SupplierRequest
from app.models.supplier import Supplier
from app.tasks.parsing_tasks import parse_pricelist_task
from sqlalchemy import select, func
from typing import Optional, Dict, Any
from uuid import UUID
import json
import os
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=SupplierRequestResponse)
async def create_supplier_request(
    data: str = Form(...),  # JSON string с данными поставщика
    contact_email: Optional[str] = Form(None),
    contact_phone: Optional[str] = Form(None),
    contact_telegram: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    pricelists: List[UploadFile] = File([]),
    db: AsyncSession = Depends(get_db)
):
    """Создать заявку на добавление поставщика (публичный endpoint)"""
    
    # Парсим JSON данные
    try:
        supplier_data = json.loads(data)
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    # Сохраняем прайс-лист в MinIO (если есть)
    pricelist_filename = None
    pricelist_url = None
    
    if pricelist:
        # TODO: Загрузка в MinIO
        # Пока сохраняем локально
        upload_dir = "/app/uploads/requests"
        os.makedirs(upload_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pricelist_filename = pricelist.filename
        filepath = os.path.join(upload_dir, f"{timestamp}_{pricelist_filename}")
        
        content = await pricelist.read()
        with open(filepath, "wb") as f:
            f.write(content)
        
        pricelist_url = filepath
    
    # Создаём заявку
    request = SupplierRequest(
        data=supplier_data,
        pricelist_filename=pricelist_filename,
        pricelist_url=pricelist_url,
        contact_email=contact_email,
        contact_phone=contact_phone,
        contact_telegram=contact_telegram,
        notes=notes,
        status="pending"
    )
    
    db.add(request)
    await db.commit()
    await db.refresh(request)
    
    # TODO: Отправить уведомления админам (Telegram + Email)
    
    return request

@router.get("/", response_model=Dict)
async def list_supplier_requests(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Получить список заявок (для админа)"""
    
    query = select(SupplierRequest)
    if status:
        query = query.where(SupplierRequest.status == status)
    
    query = query.order_by(SupplierRequest.created_at.desc())
    
    total_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(total_query)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    requests = result.scalars().all()
    
    return {
        "total": total or 0,
        "requests": [SupplierRequestResponse.from_orm(r) for r in requests],
        "page": skip // limit + 1,
        "page_size": limit
    }

@router.get("/{request_id}", response_model=SupplierRequestResponse)
async def get_supplier_request(request_id: UUID, db: AsyncSession = Depends(get_db)):
    """Получить заявку по ID"""
    
    result = await db.execute(
        select(SupplierRequest).where(SupplierRequest.id == request_id)
    )
    request = result.scalar_one_or_none()
    
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    return request

@router.post("/{request_id}/approve")
async def approve_supplier_request(
    request_id: UUID,
    admin_email: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Одобрить заявку и создать поставщика"""
    
    # Получаем заявку
    result = await db.execute(
        select(SupplierRequest).where(SupplierRequest.id == request_id)
    )
    request = result.scalar_one_or_none()
    
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if request.status != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")
    
    # Создаём поставщика
    supplier = Supplier(**request.data)
    db.add(supplier)
    await db.commit()
    await db.refresh(supplier)
    
    # Если есть прайс-лист - запускаем парсинг
    if request.pricelist_url:
        with open(request.pricelist_url, "rb") as f:
            content = f.read()
        
        # Создаём запись импорта
        from app.models.product_import import ProductImport
        
        import_record = ProductImport(
            supplier_id=supplier.id,
            file_name=request.pricelist_filename,
            file_url=request.pricelist_url,
            file_size=len(content),
            status="pending",
            total_products=0,
            parsed_products=0
        )
        
        db.add(import_record)
        await db.commit()
        await db.refresh(import_record)
        
        # Запускаем парсинг
        task = parse_pricelist_task.delay(str(supplier.id), request.pricelist_filename, content)
        import_record.task_id = task.id
        await db.commit()
    
    # Обновляем статус заявки
    request.status = "approved"
    request.reviewed_at = datetime.utcnow()
    request.reviewed_by = admin_email
    await db.commit()
    
    # TODO: Отправить уведомление заявителю
    
    return {
        "success": True,
        "supplier_id": str(supplier.id),
        "message": "Supplier approved and created"
    }

@router.post("/{request_id}/reject")
async def reject_supplier_request(
    request_id: UUID,
    admin_email: str = Form(...),
    reason: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Отклонить заявку"""
    
    result = await db.execute(
        select(SupplierRequest).where(SupplierRequest.id == request_id)
    )
    request = result.scalar_one_or_none()
    
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if request.status != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")
    
    # Обновляем статус
    request.status = "rejected"
    request.reviewed_at = datetime.utcnow()
    request.reviewed_by = admin_email
    request.rejection_reason = reason
    await db.commit()
    
    # TODO: Отправить уведомление заявителю
    
    return {
        "success": True,
        "message": "Request rejected"
    }

@router.get("/{request_id}/download")
async def download_pricelist(request_id: UUID, db: AsyncSession = Depends(get_db)):
    """Скачать прайс-лист из заявки"""
    from fastapi.responses import FileResponse
    
    result = await db.execute(
        select(SupplierRequest).where(SupplierRequest.id == request_id)
    )
    request = result.scalar_one_or_none()
    
    if not request or not request.pricelist_url:
        raise HTTPException(status_code=404, detail="Pricelist not found")
    
    if not os.path.exists(request.pricelist_url):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        request.pricelist_url,
        media_type='application/octet-stream',
        filename=request.pricelist_filename
    )
