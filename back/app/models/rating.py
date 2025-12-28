from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Rating(BaseModel):
    __tablename__ = "ratings"
    
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True)
    manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Ratings (1-5)
    price_score = Column(Integer, nullable=False)
    speed_score = Column(Integer, nullable=False)
    quality_score = Column(Integer, nullable=False)
    
    # Comment
    comment = Column(Text)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="ratings")
    manager = relationship("User", back_populates="ratings")
    
    def __repr__(self):
        return f"<Rating for supplier_id={self.supplier_id} by manager_id={self.manager_id}>"
