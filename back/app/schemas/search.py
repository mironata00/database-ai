from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    supplier_ids: Optional[List[UUID]] = None
    brands: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    status_filter: Optional[List[str]] = None
    limit: int = Field(default=100, ge=1, le=1000)


class SearchResponse(BaseModel):
    total_suppliers: int
    total_products: int
    suppliers: List[dict]
    query: str
    search_time_ms: float
