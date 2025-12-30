from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import Base
import uuid
from datetime import datetime

class SupplierRequest(Base):
    __tablename__ = "supplier_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String(20), default="pending", nullable=False)
    data = Column(JSONB, nullable=False)
    pricelist_filename = Column(String(500))
    pricelist_url = Column(String(1000))
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    contact_telegram = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime)
    reviewed_by = Column(String(255))
    rejection_reason = Column(Text)
    notes = Column(Text)
