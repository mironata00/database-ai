from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from app.models.supplier import SupplierStatus


class SupplierBase(BaseModel):
    name: str = Field(..., max_length=500)
    inn: str = Field(..., min_length=10, max_length=12)
    kpp: Optional[str] = Field(None, min_length=9, max_length=9)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    contact_person: Optional[str] = None
    contact_position: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    legal_address: Optional[str] = None
    actual_address: Optional[str] = None
    delivery_regions: Optional[List[str]] = None
    payment_terms: Optional[str] = None
    min_order_sum: Optional[Decimal] = None
    notes: Optional[str] = None
    categories: Optional[List[str]] = []
    color: Optional[str] = '#3B82F6'

    @validator('website', pre=True, always=True)
    def validate_website(cls, v):
        if not v or v.strip() == '':
            return None
        v = v.strip()
        if not v.startswith(('http://', 'https://')):
            v = 'http://' + v
        return v


class SupplierCreate(SupplierBase):
    status: SupplierStatus = SupplierStatus.PENDING


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    contact_person: Optional[str] = None
    contact_position: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    status: Optional[SupplierStatus] = None
    legal_address: Optional[str] = None
    actual_address: Optional[str] = None
    delivery_regions: Optional[List[str]] = None
    payment_terms: Optional[str] = None
    min_order_sum: Optional[Decimal] = None
    notes: Optional[str] = None
    rating: Optional[float] = None
    tags_array: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    color: Optional[str] = None


class SupplierResponse(SupplierBase):
    id: UUID
    status: SupplierStatus
    rating: Optional[float] = None
    is_blacklisted: bool = False
    tags_array: Optional[List[str]] = None
    categories: Optional[List[str]] = []
    raw_data_url: Optional[str] = None
    import_source: Optional[str] = None
    color: str = '#3B82F6'
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SupplierSearchResponse(BaseModel):
    supplier: SupplierResponse
    matched_products: int
    example_product: Optional[dict] = None
    relevance_score: float
    avg_price: Optional[float] = None


class SupplierListResponse(BaseModel):
    total: int
    suppliers: List[SupplierResponse]
    page: int = 1
    page_size: int = 100


class ExternalRegistrationRequest(SupplierBase):
    pass