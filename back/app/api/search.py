from fastapi import APIRouter, Depends, HTTPException
from app.core.elasticsearch import es_manager
from app.core.database import get_read_db
from app.schemas.search import SearchRequest, SearchResponse
from app.models.supplier import Supplier
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import time

router = APIRouter()

@router.post("/", response_model=SearchResponse)
async def search_suppliers(search_req: SearchRequest, db: AsyncSession = Depends(get_read_db)):
    start_time = time.time()
    
    filters = {
        "supplier_ids": search_req.supplier_ids,
        "brands": search_req.brands,
        "categories": search_req.categories,
        "min_price": search_req.min_price,
        "max_price": search_req.max_price,
    }
    
    es_response = await es_manager.search_products(
        query=search_req.query,
        filters=filters,
        size=search_req.limit
    )
    
    suppliers_data = []
    total_products = es_response.get("hits", {}).get("total", {}).get("value", 0)
    
    for bucket in es_response.get("aggregations", {}).get("suppliers", {}).get("buckets", []):
        supplier_id = bucket["key"]
        matched_count = bucket["doc_count"]
        avg_price = bucket.get("avg_price", {}).get("value")
        
        result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
        supplier = result.scalar_one_or_none()
        
        if supplier:
            top_hit = bucket["top_product"]["hits"]["hits"][0]["_source"]
            suppliers_data.append({
                "supplier_id": supplier_id,
                "supplier_name": supplier.name,
                "supplier_inn": supplier.inn,
                "supplier_status": supplier.status.value,
                "matched_products": matched_count,
                "example_product": top_hit,
                "avg_price": avg_price,
                "relevance_score": bucket.get("score", 0)
            })
    
    suppliers_data.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    search_time = (time.time() - start_time) * 1000
    
    return {
        "total_suppliers": len(suppliers_data),
        "total_products": total_products,
        "suppliers": suppliers_data[:search_req.limit],
        "query": search_req.query,
        "search_time_ms": search_time
    }
