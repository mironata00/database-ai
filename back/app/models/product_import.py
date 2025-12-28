from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class ImportStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProductImport(BaseModel):
    __tablename__ = "product_imports"
    __table_args__ = {'extend_existing': True}

    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True)
    file_url = Column(String(1000))
    file_name = Column(String(500))
    file_size = Column(Integer)
    status = Column(String(50), default='pending', index=True)
    total_products = Column(Integer, default=0)
    parsed_products = Column(Integer, default=0)
    error_message = Column(Text)
    completed_at = Column(DateTime)

    # Relationship
    supplier = relationship("Supplier", back_populates="product_imports")

    def __repr__(self):
        return f"<ProductImport {self.file_name} ({self.status})>"
