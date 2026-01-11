import logging
from app.api.auth import get_current_user_dependency
logger = logging.getLogger(__name__)
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
        return '#6B7280'
    elif len(categories) == 1:
        category_key = categories[0]
        return SUPPLIER_CATEGORIES.get(category_key, {}).get('color', '#6B7280')
    else:
        return MULTI_CATEGORY_COLOR

@router.get("/search")
async def search_suppliers_intelligent(
    q: str = Query(..., min_length=2, description="Поисковый запрос"),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db)
):
    """
    Интеллектуальный поиск по поставщикам с приоритетами:
    1. Точное вхождение ВСЕХ слов
    2. Морфологическое совпадение ВСЕХ слов
    3. Точное вхождение ЛЮБОГО слова
    4. Морфологическое совпадение ЛЮБОГО слова
    """

    # Если Elasticsearch отключен
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
                    "all_products": [],
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
    all_products_by_supplier = {}
    
    query_lower = q.lower()
    query_words = [w for w in query_lower.split() if len(w) >= 2]
    
    # Простой стемминг
    def simple_stem(word):
        endings = ["ами", "ией", "ому", "ему", "ого", "его", "ая", "яя", "ой", "ый", "ий", "ые", "ие", "ую", "юю", "ою", "ью", "ев", "ов", "ам", "ем", "ом", "их", "ых", "ию", "ей", "ое", "ее"]
        for end in endings:
            if word.endswith(end) and len(word) > len(end) + 2:
                return word[:-len(end)]
        return word

    query_stems = [simple_stem(w) for w in query_words]

    for hit in es_response.get("hits", {}).get("hits", []):
        source = hit["_source"]
        supplier_id = source.get("supplier_id")
        score = hit.get("_score", 0)
        
        product_name = (source.get("name") or "").lower()
        product_words = [w for w in product_name.split() if len(w) >= 2]
        product_stems = [simple_stem(w) for w in product_words]
        
        # ПРИОРИТЕТ 1: Точное вхождение ВСЕХ слов
        exact_match_all = all(word in product_name for word in query_words)
        
        # ПРИОРИТЕТ 2: Морфология ВСЕХ слов
        morph_match_all = len(query_stems) > 1 and all(
            any(q_stem in p_stem or p_stem in q_stem for p_stem in product_stems)
            for q_stem in query_stems
        )
        
        # ПРИОРИТЕТ 3: Точное вхождение ЛЮБОГО слова
        exact_match_any = any(word in product_name for word in query_words)
        
        # ПРИОРИТЕТ 4: Морфология ЛЮБОГО слова
        morph_match_any = any(
            any(q_stem in p_stem or p_stem in q_stem for p_stem in product_stems)
            for q_stem in query_stems
        )
        
        if exact_match_all:
            match_category = 1
        elif morph_match_all:
            match_category = 2
        elif exact_match_any:
            match_category = 3
        elif morph_match_any:
            match_category = 4
        else:
            match_category = 5
        
        product_data = {
            "sku": source.get("sku"),
            "name": source.get("name"),
            "price": source.get("price"),
            "brand": source.get("brand"),
            "score": score,
            "supplier_id": supplier_id,
            "match_category": match_category
        }

        if supplier_id:
            if supplier_id not in all_products_by_supplier:
                all_products_by_supplier[supplier_id] = []
            all_products_by_supplier[supplier_id].append(product_data)

            if supplier_id not in supplier_stats:
                supplier_stats[supplier_id] = {
                    "matched_count": 0,
                    "max_score": 0,
                    "example_products": []
                }

            supplier_stats[supplier_id]["matched_count"] += 1
            supplier_stats[supplier_id]["max_score"] = max(supplier_stats[supplier_id]["max_score"], score)

            if len(supplier_stats[supplier_id]["example_products"]) < 2:
                supplier_stats[supplier_id]["example_products"].append({
                    "sku": source.get("sku"),
                    "name": source.get("name"),
                    "price": source.get("price"),
                    "brand": source.get("brand"),
                    "score": score
                })

    # Fallback на БД
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
                    "all_products": [],
                    "match_type": "supplier_name_or_tags"
                }
                for s in suppliers
            ]
        }

    # Поиск по тегам в БД
    query_pattern = f"%{q.lower()}%"
    result_tags = await db.execute(
        select(Supplier).where(
            or_(
                Supplier.name.ilike(query_pattern),
                func.array_to_string(Supplier.tags_array, ',').ilike(query_pattern)
            )
        )
    )
    suppliers_by_tags = result_tags.scalars().all()
    
    for supplier in suppliers_by_tags:
        supplier_id_str = str(supplier.id)
        if supplier_id_str not in supplier_stats:
            supplier_stats[supplier_id_str] = {
                "matched_count": 0,
                "max_score": 100.0,
                "example_products": [],
                "matched_by_tag": True
            }
            all_products_by_supplier[supplier_id_str] = []

    supplier_ids_list = list(supplier_stats.keys())
    result = await db.execute(
        select(Supplier).where(Supplier.id.in_(supplier_ids_list))
    )
    suppliers = {str(s.id): s for s in result.scalars().all()}

    results = []
    for supplier_id, stats in supplier_stats.items():
        supplier = suppliers.get(supplier_id)
        if supplier:
            match_type = "supplier_tags" if stats.get("matched_by_tag") else "products"
            
            # Сортируем товары по приоритету
            supplier_products = all_products_by_supplier.get(supplier_id, [])
            supplier_products.sort(key=lambda p: (p["match_category"], -p["score"]))
            
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
                "all_products": supplier_products,
                "match_type": match_type
            })

    # Сортировка результатов
    results.sort(
        key=lambda x: (
            x["supplier_rating"] if x["supplier_rating"] is not None else -1,
            x["max_score"] * max(x["matched_products"], 1)
        ), 
        reverse=True
    )

    # Агрегация тегов
    from collections import Counter
    import re as regex_module
    
    tag_counter = Counter()
    
    for products_list in all_products_by_supplier.values():
        for product in products_list:
            name = (product.get("name") or "").lower()
            name = regex_module.sub(r'[^\w\s]', ' ', name)
            words = name.split()
            
            for i in range(len(words)):
                for length in range(1, 4):
                    if i + length <= len(words):
                        tag = ' '.join(words[i:i+length])
                        if len(tag) >= 3:
                            tag_counter[tag] += 1
    
    for supplier_id, stats in supplier_stats.items():
        if stats.get("matched_by_tag"):
            supplier = suppliers.get(supplier_id)
            if supplier and supplier.tags_array:
                for tag in supplier.tags_array:
                    if len(tag) >= 3:
                        tag_counter[tag] += 50
    
    def calculate_tag_relevance(tag, query_lower, query_words):
        tag_lower = tag.lower()
        
        if tag_lower == query_lower:
            return 1000
        if tag_lower.startswith(query_lower):
            return 900
        if query_lower in tag_lower:
            return 800
        
        tag_words = set(tag_lower.split())
        query_words_set = set(query_words)
        
        if query_words_set.issubset(tag_words):
            return 700
        
        matching_words = len(query_words_set & tag_words)
        if matching_words > 0:
            return 500 + (matching_words * 50)
        
        for qword in query_words:
            for tword in tag_words:
                if qword in tword or tword in qword:
                    return 300
        
        return 0
    
    tags_with_score = []
    for tag, count in tag_counter.items():
        if count >= 3:
            relevance = calculate_tag_relevance(tag, query_lower, query_words)
            tags_with_score.append({
                "tag": tag,
                "count": count,
                "relevance": relevance
            })
    
    tags_with_score.sort(key=lambda x: (x["relevance"], x["count"]), reverse=True)
    top_tags = tags_with_score[:50]

    # Собираем ВСЕ уникальные товары с приоритизацией
    all_unique_products = []
    seen_product_keys = set()
    
    for products_list in all_products_by_supplier.values():
        for product in products_list:
            key = f"{product.get('sku', '')}_{product.get('name', '')}"
            if key not in seen_product_keys:
                seen_product_keys.add(key)
                all_unique_products.append(product)
    
    # Сортируем товары по приоритету: сначала match_category (1-5), потом score
    all_unique_products.sort(key=lambda p: (p["match_category"], -p["score"]))

    return {
        "total": len(results),
        "query": q,
        "search_mode": "elasticsearch",
        "results": results[:limit],
        "top_tags": top_tags,
        "all_products": all_unique_products
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
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    update_data = supplier_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(supplier, key):
            setattr(supplier, key, value)

    await db.commit()
    await db.refresh(supplier)

    if 'tags_array' in update_data and settings.SEARCH_ELASTICSEARCH_ENABLED:
        try:
            result = await es_manager.update_supplier_tags(
                str(supplier_id),
                supplier.tags_array or []
            )
            logger.info(f"Updated tags in ES for {supplier.name}: {result.get('updated', 0)} products")
        except Exception as e:
            logger.error(f"Ошибка обновления тегов в ES: {e}")

    return SupplierResponse.from_orm(supplier)

@router.delete("/{supplier_id}")
async def delete_supplier(supplier_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
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
    
    await db.delete(supplier)
    await db.commit()
    
    return {"deleted": True, "supplier_id": str(supplier_id), "name": supplier.name}

@router.get("/{supplier_id}/imports")
async def get_supplier_imports(supplier_id: UUID, db: AsyncSession = Depends(get_db)):
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


# EMAIL HISTORY ENDPOINT
@router.get("/{supplier_id}/email-history")
async def get_supplier_email_history(
    supplier_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency)
):
    """Получить историю переписки с поставщиком, сгруппированную по threads"""
    from app.models.email import EmailThread, EmailDirection
    from sqlalchemy import desc
    from collections import defaultdict
    import re

    # Проверяем существование поставщика
    result = await db.execute(
        select(Supplier).where(Supplier.id == supplier_id)
    )
    supplier = result.scalar_one_or_none()

    if not supplier:
        raise HTTPException(status_code=404, detail="Поставщик не найден")

    # Получаем всю историю переписки
    result = await db.execute(
        select(EmailThread)
        .where(EmailThread.supplier_id == supplier_id)
        .order_by(EmailThread.created_at)
    )
    email_threads = result.scalars().all()

    # Функция для нормализации subject
    def normalize_subject(subject):
        if not subject:
            return ""
        s = subject.lower().strip()
        # Убираем Re:, Fwd:, Fw: и пробелы
        while True:
            old = s
            s = re.sub(r'^(re:|fwd:|fw:)\s*', '', s, flags=re.IGNORECASE).strip()
            if s == old:
                break
        return s

    # Группируем по subject
    threads_by_subject = defaultdict(list)
    
    for thread in email_threads:
        normalized = normalize_subject(thread.subject)
        threads_by_subject[normalized].append({
            "id": str(thread.id),
            "message_id": thread.message_id,
            "subject": thread.subject,
            "from_addr": thread.from_addr,
            "to_addr": thread.to_addr,
            "cc_addr": thread.cc_addr,
            "bcc_addr": thread.bcc_addr,
            "body_text": thread.body_text,
            "body_html": thread.body_html,
            "direction": thread.direction.value,
            "attachments": thread.attachments,
            "in_reply_to": thread.in_reply_to,
            "created_at": thread.created_at.isoformat() if thread.created_at else None,
            "updated_at": thread.updated_at.isoformat() if thread.updated_at else None
        })

    # Формируем результат
    grouped_threads = []
    for normalized_subject, messages in threads_by_subject.items():
        # Сортируем сообщения по времени
        messages.sort(key=lambda x: x['created_at'] or '')
        
        grouped_threads.append({
            "subject": messages[0]['subject'],
            "normalized_subject": normalized_subject,
            "message_count": len(messages),
            "messages": messages,
            "last_message_at": messages[-1]['created_at'] if messages else None
        })
    
    # Сортируем threads по последнему сообщению
    grouped_threads.sort(key=lambda x: x['last_message_at'] or '', reverse=True)

    return {
        "supplier_id": str(supplier_id),
        "supplier_name": supplier.name,
        "supplier_email": supplier.contact_email or supplier.email,
        "total_threads": len(grouped_threads),
        "total_messages": sum(t['message_count'] for t in grouped_threads),
        "threads": grouped_threads
    }

