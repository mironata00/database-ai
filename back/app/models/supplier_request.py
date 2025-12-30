from sqlalchemy import Column, String, TIMESTAMP, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.models.base import BaseModel
import uuid
from datetime import datetime

class SupplierRequest(BaseModel):
    __tablename__ = "supplier_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String(20), nullable=False, default="pending")
    data = Column(JSONB, nullable=False)
    
    pricelist_filenames = Column(ARRAY(String), nullable=True)
    pricelist_urls = Column(ARRAY(String), nullable=True)
    
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    contact_telegram = Column(String(100), nullable=True)
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    reviewed_at = Column(TIMESTAMP, nullable=True)
    reviewed_by = Column(String(255), nullable=True)
    
    rejection_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
