from pydantic import BaseModel
from typing import List, Optional

class ProductItem(BaseModel):
    name: str
    sku: Optional[str] = None

class PriceRequestCreate(BaseModel):
    products: List[ProductItem]
    supplier_ids: List[str]
    subject: str
    body: str

class PriceRequestResponse(BaseModel):
    success: bool
    sent_count: int
    failed_count: int
    details: List[dict]
