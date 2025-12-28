from sqlalchemy import Column, String, Text, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class AuditAction(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    IMPORT = "import"


class AuditLog(BaseModel):
    __tablename__ = "audit_logs"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    
    action = Column(SQLEnum(AuditAction), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(100))
    
    # What changed
    old_values = Column(JSON)
    new_values = Column(JSON)
    
    # Request metadata
    ip_address = Column(INET)
    user_agent = Column(String(500))
    endpoint = Column(String(500))
    
    # Additional context
    description = Column(Text)
    extra_metadata = Column(JSON)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog {self.action} on {self.entity_type} by user_id={self.user_id}>"
