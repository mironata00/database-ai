from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.auth import get_current_user
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/pending-imports")
async def get_pending_imports(db: AsyncSession = Depends(get_db)):
    return {"message": "Pending imports endpoint - implementation in progress"}

@router.post("/pending-imports/{import_id}/approve")
async def approve_import(import_id: str, db: AsyncSession = Depends(get_db)):
    return {"message": f"Approving import {import_id}"}

@router.post("/reindex-all")
async def reindex_all_products(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Пересоздать индекс ElasticSearch и переиндексировать все товары"""
    from app.core.elasticsearch import es_manager
    from app.models.supplier import Supplier
    from app.models.product import Product
    from sqlalchemy import select
    
    try:
        # Удаляем старый индекс
        await es_manager.client.indices.delete(index='products', ignore=[404])
        logger.info("Старый индекс удален")
        
        # Создаем новый с ngram
        await es_manager.create_products_index()
        logger.info("Новый индекс создан с ngram анализатором")
        
        # Получаем всех активных поставщиков
        result = await db.execute(select(Supplier).where(Supplier.status == 'ACTIVE'))
        suppliers = result.scalars().all()
        
        total_indexed = 0
        failed_suppliers = []
        
        for supplier in suppliers:
            try:
                result = await db.execute(
                    select(Product).where(Product.supplier_id == supplier.id)
                )
                products = result.scalars().all()
                
                if not products:
                    continue
                
                products_data = []
                for product in products:
                    products_data.append({
                        "supplier_id": str(supplier.id),
                        "supplier_name": supplier.name,
                        "supplier_inn": supplier.inn,
                        "sku": product.sku or "",
                        "name": product.name or "",
                        "brand": product.brand or "",
                        "category": product.category or "",
                        "tags": [],
                        "price": float(product.price) if product.price else None,
                        "unit": product.unit or "",
                        "raw_text": product.raw_text or "",
                        "last_updated": product.updated_at.isoformat() if product.updated_at else None,
                    })
                
                result_index = await es_manager.bulk_index_products(products_data, str(supplier.id))
                total_indexed += result_index.get('success', 0)
                
                logger.info(f"Проиндексировано {result_index.get('success', 0)} товаров для {supplier.name}")
                
            except Exception as e:
                logger.error(f"Ошибка индексации поставщика {supplier.name}: {e}")
                failed_suppliers.append(supplier.name)
        
        return {
            "success": True,
            "message": "Реиндексация завершена",
            "total_indexed": total_indexed,
            "total_suppliers": len(suppliers),
            "failed_suppliers": failed_suppliers
        }
        
    except Exception as e:
        logger.error(f"Ошибка реиндексации: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка реиндексации: {str(e)}")
