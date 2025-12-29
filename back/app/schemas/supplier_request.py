from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class SupplierRequestCreate(BaseModel):
    data: Dict[str, Any]  # Все поля поставщика
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    contact_telegram: Optional[str] = None
    notes: Optional[str] = None

class SupplierRequestResponse(BaseModel):
    id: UUID
    status: str
    data: Dict[str, Any]
    pricelist_filename: Optional[str]
    pricelist_url: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    contact_telegram: Optional[str]
    created_at: datetime
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[str]
    rejection_reason: Optional[str]
    notes: Optional[str]

    class Config:
        from_attributes = True

class SupplierRequestUpdate(BaseModel):
    status: Optional[str] = None
    reviewed_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None
