from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class SupplierRequestCreate(BaseModel):
    data: dict
    pricelist_filenames: Optional[List[str]] = None
    pricelist_urls: Optional[List[str]] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_telegram: Optional[str] = None
    notes: Optional[str] = None

class SupplierRequestResponse(BaseModel):
    id: UUID
    status: str
    data: dict
    pricelist_filenames: Optional[List[str]] = None
    pricelist_urls: Optional[List[str]] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_telegram: Optional[str] = None
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True

class SupplierRequestUpdate(BaseModel):
    status: Optional[str] = None
