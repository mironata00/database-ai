"""
Модель Product - товары из прайс-листов
"""
from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Product(BaseModel):
    """Товары из прайс-листов поставщиков"""
    __tablename__ = "products"
    __table_args__ = (
        Index('idx_product_text_search', 'name', 'sku', postgresql_using='gin'),
        {'extend_existing': True}
    )
    
    # Foreign keys
    supplier_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("suppliers.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    import_id = Column(
        UUID(as_uuid=True),
        ForeignKey("product_imports.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Основные поля
    sku = Column(String(255), index=True)
    name = Column(Text, nullable=False)
    brand = Column(String(255), index=True)
    category = Column(String(255), index=True)
    
    # Цена и остатки
    price = Column(Float)
    old_price = Column(Float)
    unit = Column(String(50))
    stock = Column(Integer)
    min_order = Column(Float)
    
    # Дополнительно
    description = Column(Text)
    specifications = Column(JSON)
    barcode = Column(String(100))
    vendor_code = Column(String(100))
    raw_text = Column(Text)
    row_number = Column(Integer)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="products")
    product_import = relationship("ProductImport", back_populates="products")
    
    def __repr__(self):
        return f"<Product {self.sku}: {self.name[:50]}>"
