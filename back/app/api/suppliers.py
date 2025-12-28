from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from app.models.product_import import ProductImport
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.supplier import SupplierCreate, SupplierUpdate, SupplierResponse, SupplierListResponse
from app.models.supplier import Supplier
from app.tasks.parsing_tasks import parse_pricelist_task
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID

router = APIRouter()

@router.get("/", response_model=SupplierListResponse)
async def list_suppliers(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Supplier)
    if status:
        query = query.where(Supplier.status == status)
    
    total_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(total_query)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    suppliers = result.scalars().all()
    
    return {
        "total": total or 0,
        "suppliers": [SupplierResponse.from_orm(s) for s in suppliers],
        "page": skip // limit + 1,
        "page_size": limit
    }

@router.post("/", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(supplier_data: SupplierCreate, db: AsyncSession = Depends(get_db)):
    supplier = Supplier(**supplier_data.dict())
    db.add(supplier)
    await db.commit()
    await db.refresh(supplier)
    return SupplierResponse.from_orm(supplier)

@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(supplier_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return SupplierResponse.from_orm(supplier)

@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(supplier_id: UUID, supplier_data: SupplierUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    for key, value in supplier_data.dict(exclude_unset=True).items():
        setattr(supplier, key, value)
    
    await db.commit()
    await db.refresh(supplier)
    return SupplierResponse.from_orm(supplier)

@router.post("/{supplier_id}/upload-pricelist")
async def upload_pricelist(supplier_id: UUID, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    task = parse_pricelist_task.delay(str(supplier_id), file.filename, await file.read())
    return {"task_id": task.id, "status": "processing"}


@router.patch("/{supplier_id}", response_model=SupplierResponse)
async def patch_supplier(supplier_id: UUID, supplier_data: SupplierUpdate, db: AsyncSession = Depends(get_db)):
    """Частичное обновление поставщика"""
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    for key, value in supplier_data.dict(exclude_unset=True).items():
        setattr(supplier, key, value)
    
    await db.commit()
    await db.refresh(supplier)
    return SupplierResponse.from_orm(supplier)


@router.get("/{supplier_id}/imports")
async def get_supplier_imports(supplier_id: UUID, db: AsyncSession = Depends(get_db)):
    """Получить историю импортов"""
    from app.models.product_import import ProductImport
    
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    result = await db.execute(
        select(ProductImport)
        .where(ProductImport.supplier_id == supplier_id)
        .order_by(ProductImport.created_at.desc())
    )
    imports = result.scalars().all()
    
    return {
        "imports": [
            {
                "id": str(imp.id),
                "file_name": imp.file_name,
                "file_url": imp.file_url,
                "status": imp.status,
                "total_products": imp.total_products or 0,
                "parsed_products": imp.parsed_products or 0,
                "created_at": imp.created_at.isoformat() if imp.created_at else None,
                "error_message": imp.error_message
            }
            for imp in imports
        ]
    }

@router.post("/{supplier_id}/upload-pricelist-new")
async def upload_pricelist_new(supplier_id: UUID, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """Загрузить прайс-лист (новая версия)"""
    from app.models.product_import import ProductImport
    import os
    from datetime import datetime
    
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Создать директорию
    upload_dir = f"/app/uploads/{supplier_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Сохранить файл
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    filepath = os.path.join(upload_dir, filename)
    
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    
    # Создать запись в БД
    import_record = ProductImport(
        supplier_id=supplier_id,
        file_name=file.filename,
        file_url=filepath,
        file_size=len(content),
        status="pending",
        total_products=0,
        parsed_products=0
    )
    
    db.add(import_record)
    await db.commit()
    await db.refresh(import_record)
    
    return {"import_id": str(import_record.id), "status": "uploaded", "file_url": filepath}


@router.post("/{supplier_id}/upload-pricelist-new")
async def upload_pricelist_new(supplier_id: UUID, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """Загрузить прайс-лист (новая версия)"""
    from app.models.product_import import ProductImport
    import os
    from datetime import datetime
    
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Создать директорию
    upload_dir = f"/app/uploads/{supplier_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Сохранить файл
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    filepath = os.path.join(upload_dir, filename)
    
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    
    # Создать запись в БД
    import_record = ProductImport(
        supplier_id=supplier_id,
        file_name=file.filename,
        file_url=filepath,
        file_size=len(content),
        status="pending",
        total_products=0,
        parsed_products=0
    )
    
    db.add(import_record)
    await db.commit()
    await db.refresh(import_record)
    
    return {"import_id": str(import_record.id), "status": "uploaded", "file_url": filepath}
