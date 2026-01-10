from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from app.models.product_import import ProductImport
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.elasticsearch import es_manager
from app.core.config import settings, SUPPLIER_CATEGORIES, MULTI_CATEGORY_COLOR
from app.schemas.supplier import SupplierCreate, SupplierUpdate, SupplierResponse, SupplierListResponse
from app.models.supplier import Supplier
from app.tasks.parsing_tasks import parse_pricelist_task
from sqlalchemy import select, func, or_
from typing import List, Optional
from uuid import UUID

router = APIRouter()

@router.get("/categories")
async def get_categories():
    """Получить список всех категорий с цветами"""
    return {
        "categories": SUPPLIER_CATEGORIES,
        "multi_category_color": MULTI_CATEGORY_COLOR
    }

def get_supplier_display_color(categories: List[str]) -> str:
    """
    Вычислить цвет для отображения поставщика на основе направлений
    
    Логика:
    - 0 категорий → серый (#6B7280)
    - 1 категория → цвет этой категории
    - 2+ категории → черный (#000000)
    """
    if not categories or len(categories) == 0:
        return '#6B7280'  # Серый для поставщиков без направления
    elif len(categories) == 1:
        category_key = categories[0]
        return SUPPLIER_CATEGORIES.get(category_key, {}).get('color', '#6B7280')
    else:
        return MULTI_CATEGORY_COLOR  # Черный для множественных направлений

@router.get("/search")
async def search_suppliers_intelligent(
    q: str = Query(..., min_length=2, description="Поисковый запрос"),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db)
):
    """
    Интеллектуальный поиск по поставщикам
    Использует Elasticsearch если включен, иначе простой поиск по БД
    """

    # Если Elasticsearch отключен - используем простой поиск по БД
    if not settings.SEARCH_ELASTICSEARCH_ENABLED:
        query_pattern = f"%{q.lower()}%"
        result = await db.execute(
            select(Supplier).where(
                or_(
                    Supplier.name.ilike(query_pattern),
                    func.array_to_string(Supplier.tags_array, ',').ilike(query_pattern)
                )
            ).limit(limit)
        )
        suppliers = result.scalars().all()

        return {
            "total": len(suppliers),
            "query": q,
            "search_mode": "database",
            "results": [
                {
                    "supplier_id": str(s.id),
                    "supplier_name": s.name,
                    "supplier_inn": s.inn,
                    "supplier_status": s.status.value if hasattr(s.status, 'value') else s.status,
                    "supplier_rating": s.rating,
                    "supplier_tags": s.tags_array or [],
                    "supplier_categories": s.categories or [],
                    "supplier_color": get_supplier_display_color(s.categories or []),
                    "matched_products": 0,
                    "max_score": 0,
                    "example_products": [],
                    "match_type": "supplier_name_or_tags"
                }
                for s in suppliers
            ]
        }

    # Elasticsearch поиск
    es_response = await es_manager.search_products(
        query=q,
        filters={},
        size=1000
    )

    supplier_stats = {}
    all_products = []  # Все найденные товары
    
    # Определяем ключевые слова запроса для точного совпадения
    query_lower = q.lower()
    query_words = set(query_lower.split())

    for hit in es_response.get("hits", {}).get("hits", []):
        source = hit["_source"]
        supplier_id = source.get("supplier_id")
        score = hit.get("_score", 0)
        
        # Определяем точное совпадение (если название содержит ВСЕ слова запроса)
        product_name = (source.get("name") or "").lower()
        product_brand = (source.get("brand") or "").lower()
        product_sku = (source.get("sku") or "").lower()
        
        # Точное совпадение если:
        # 1. Все слова запроса есть в названии
        # 2. ИЛИ бренд точно совпадает И хотя бы одно слово в названии
        is_exact_match = (
            all(word in product_name for word in query_words) or
            all(word in product_sku for word in query_words) or
            (query_lower in product_brand and any(word in product_name for word in query_words))
        )

        # Собираем все товары
        all_products.append({
            "sku": source.get("sku"),
            "name": source.get("name"),
            "price": source.get("price"),
            "brand": source.get("brand"),
            "score": score,
            "supplier_id": supplier_id,
            "is_exact_match": is_exact_match
        })

        if supplier_id:
            if supplier_id not in supplier_stats:
                supplier_stats[supplier_id] = {
                    "matched_count": 0,
                    "max_score": 0,
                    "example_products": []
                }

            supplier_stats[supplier_id]["matched_count"] += 1
            supplier_stats[supplier_id]["max_score"] = max(supplier_stats[supplier_id]["max_score"], score)

            if len(supplier_stats[supplier_id]["example_products"]) < 3:
                supplier_stats[supplier_id]["example_products"].append({
                    "sku": source.get("sku"),
                    "name": source.get("name"),
                    "price": source.get("price"),
                    "brand": source.get("brand"),
                    "score": score
                })

    # Fallback на БД если ES не нашёл
    if not supplier_stats:
        query_pattern = f"%{q.lower()}%"
        result = await db.execute(
            select(Supplier).where(
                or_(
                    Supplier.name.ilike(query_pattern),
                    func.array_to_string(Supplier.tags_array, ',').ilike(query_pattern)
                )
            ).limit(limit)
        )
        suppliers = result.scalars().all()

        return {
            "total": len(suppliers),
            "query": q,
            "search_mode": "database_fallback",
            "results": [
                {
                    "supplier_id": str(s.id),
                    "supplier_name": s.name,
                    "supplier_inn": s.inn,
                    "supplier_status": s.status.value if hasattr(s.status, 'value') else s.status,
                    "supplier_rating": s.rating,
                    "supplier_tags": s.tags_array or [],
                    "supplier_categories": s.categories or [],
                    "supplier_color": get_supplier_display_color(s.categories or []),
                    "matched_products": 0,
                    "max_score": 0,
                    "example_products": [],
                    "match_type": "supplier_name_or_tags"
                }
                for s in suppliers
            ]
        }

    supplier_ids_list = list(supplier_stats.keys())
    result = await db.execute(
        select(Supplier).where(Supplier.id.in_(supplier_ids_list))
    )
    suppliers = {str(s.id): s for s in result.scalars().all()}

    results = []
    for supplier_id, stats in supplier_stats.items():
        supplier = suppliers.get(supplier_id)
        if supplier:
            results.append({
                "supplier_id": supplier_id,
                "supplier_name": supplier.name,
                "supplier_inn": supplier.inn,
                "supplier_status": supplier.status.value if hasattr(supplier.status, 'value') else supplier.status,
                "supplier_rating": supplier.rating,
                "supplier_tags": supplier.tags_array or [],
                "supplier_categories": supplier.categories or [],
                "supplier_color": get_supplier_display_color(supplier.categories or []),
                "matched_products": stats["matched_count"],
                "max_score": stats["max_score"],
                "example_products": stats["example_products"],
                "match_type": "products"
            })

    # Сортировка: сначала по рейтингу (если есть), потом по релевантности
    results.sort(
        key=lambda x: (
            x["supplier_rating"] if x["supplier_rating"] is not None else -1,  # По рейтингу
            x["max_score"] * x["matched_products"]  # Потом по релевантности
        ), 
        reverse=True
    )


    # Агрегация тегов из названий товаров
    from collections import Counter
    import re as regex_module
    
    tag_counter = Counter()
    for product in all_products:
        name = (product.get("name") or "").lower()
        # Удаляем спецсимволы
        name = regex_module.sub(r'[^\w\s]', ' ', name)
        words = name.split()
        
        # Создаём n-граммы (1-3 слова)
        for i in range(len(words)):
            for length in range(1, 4):  # 1, 2, 3 слова
                if i + length <= len(words):
                    tag = ' '.join(words[i:i+length])
                    if len(tag) >= 4:  # Минимум 4 символа
                        tag_counter[tag] += 1
    
    # Топ-50 тегов (встречаются минимум 3 раза)
    top_tags = [
        {"tag": tag, "count": count} 
        for tag, count in tag_counter.most_common(50) 
        if count >= 3
    ]

    return {
        "total": len(results),
        "query": q,
        "search_mode": "elasticsearch",
        "results": results[:limit],
        "all_products": all_products,
        "top_tags": top_tags  # Агрегированные теги
    }

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
    """Полное обновление поставщика (заменяет все поля)"""
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    for key, value in supplier_data.dict(exclude_unset=True).items():
        setattr(supplier, key, value)

    await db.commit()
    await db.refresh(supplier)
    return SupplierResponse.from_orm(supplier)

@router.patch("/{supplier_id}", response_model=SupplierResponse)
async def patch_supplier(supplier_id: UUID, supplier_data: SupplierUpdate, db: AsyncSession = Depends(get_db)):
    """Частичное обновление поставщика (обновляет только переданные поля)"""
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    # Обновляем только те поля, которые были переданы
    update_data = supplier_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(supplier, key):
            setattr(supplier, key, value)

    await db.commit()
    await db.refresh(supplier)
    return SupplierResponse.from_orm(supplier)

@router.delete("/{supplier_id}")
async def delete_supplier(supplier_id: UUID, db: AsyncSession = Depends(get_db)):
    """Удалить поставщика и все связанные данные (продукты, импорты, рейтинги)"""
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Удаляем файлы импортов
    import os
    result_imports = await db.execute(
        select(ProductImport).where(ProductImport.supplier_id == supplier_id)
    )
    imports = result_imports.scalars().all()
    for imp in imports:
        if imp.file_url and os.path.exists(imp.file_url):
            try:
                os.remove(imp.file_url)
            except Exception as e:
                print(f"Error deleting file {imp.file_url}: {e}")
    
    # Удаляем поставщика (cascade удалит products, ratings, email_threads, product_imports)
    await db.delete(supplier)
    await db.commit()
    
    return {"deleted": True, "supplier_id": str(supplier_id), "name": supplier.name}

@router.get("/{supplier_id}/imports")
async def get_supplier_imports(supplier_id: UUID, db: AsyncSession = Depends(get_db)):
    """Получить историю импортов"""
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
    import os
    from datetime import datetime

    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    upload_dir = f"/app/uploads/{supplier.inn}"
    os.makedirs(upload_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    filepath = os.path.join(upload_dir, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

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

    task = parse_pricelist_task.delay(str(supplier_id), file.filename, content)
    import_record.task_id = task.id
    await db.commit()

    return {
        "import_id": str(import_record.id),
        "task_id": task.id,
        "status": "pending",
        "file_url": filepath
    }

@router.get("/{supplier_id}/imports/{import_id}/download")
async def download_pricelist(supplier_id: UUID, import_id: UUID, db: AsyncSession = Depends(get_db)):
    """Скачать файл прайс-листа"""
    from fastapi.responses import FileResponse
    import os

    result = await db.execute(
        select(ProductImport).where(
            ProductImport.id == import_id,
            ProductImport.supplier_id == supplier_id
        )
    )
    imp = result.scalar_one_or_none()
    if not imp or not imp.file_url:
        raise HTTPException(status_code=404, detail="File not found")

    if not os.path.exists(imp.file_url):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        imp.file_url,
        media_type='application/octet-stream',
        filename=imp.file_name
    )

@router.delete("/{supplier_id}/imports/{import_id}")
async def delete_import(supplier_id: UUID, import_id: UUID, db: AsyncSession = Depends(get_db)):
    """Удалить импорт прайс-листа"""
    import os

    result = await db.execute(
        select(ProductImport).where(
            ProductImport.id == import_id,
            ProductImport.supplier_id == supplier_id
        )
    )
    imp = result.scalar_one_or_none()
    if not imp:
        raise HTTPException(status_code=404, detail="Import not found")

    if imp.file_url and os.path.exists(imp.file_url):
        os.remove(imp.file_url)

    await db.delete(imp)
    await db.commit()

    return {"deleted": True}

@router.delete("/{supplier_id}")
async def delete_supplier(supplier_id: UUID, db: AsyncSession = Depends(get_db)):
    """Удалить поставщика и все связанные данные"""
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Удаляем файлы импортов
    import os
    result_imports = await db.execute(
        select(ProductImport).where(ProductImport.supplier_id == supplier_id)
    )
    imports = result_imports.scalars().all()
    for imp in imports:
        if imp.file_url and os.path.exists(imp.file_url):
            try:
                os.remove(imp.file_url)
            except Exception:
                pass
    
    # Удаляем поставщика (cascade удалит связанные данные)
    await db.delete(supplier)
    await db.commit()
    
    return {"deleted": True, "supplier_id": str(supplier_id), "name": supplier.name}