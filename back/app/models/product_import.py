from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, JSON
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
    
    # Файл
    file_url = Column(String(1000))
    file_name = Column(String(500))
    file_size = Column(Integer)
    file_format = Column(String(20))
    
    # Статус
    status = Column(String(50), default='pending', index=True)
    total_products = Column(Integer, default=0)
    parsed_products = Column(Integer, default=0)
    error_message = Column(Text)
    completed_at = Column(DateTime)
    
    # НОВЫЕ ПОЛЯ
    task_id = Column(String(255))
    detected_columns = Column(JSON)
    generated_tags = Column(JSON)
    total_rows = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    successful_rows = Column(Integer, default=0)
    failed_rows = Column(Integer, default=0)
    indexed_to_es = Column(Integer, default=0)
    es_indexed_count = Column(Integer, default=0)

    # Relationships
    supplier = relationship("Supplier", back_populates="product_imports")
    products = relationship(
        "Product", 
        back_populates="product_import",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    def __repr__(self):
        return f"<ProductImport {self.file_name} ({self.status})>"
    
    def get_progress_percent(self) -> float:
        if self.total_rows == 0:
            return 0.0
        return round((self.processed_rows / self.total_rows) * 100, 2)
