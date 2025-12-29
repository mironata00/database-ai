from sqlalchemy import Column, String, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class UserRole(str, enum.Enum):
    admin = "admin"
    manager = "manager"
    viewer = "viewer"


class User(BaseModel):
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    
    # ИСПРАВЛЕНИЕ: Указываем имя существующего ENUM типа в БД
    role = Column(
        SQLEnum(UserRole, name='user_role', create_type=False),
        nullable=False,
        default=UserRole.viewer
    )
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    ratings = relationship("Rating", back_populates="manager", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    email_campaigns = relationship("EmailCampaign", back_populates="created_by_user", cascade="all, delete-orphan")
    email_templates = relationship("EmailTemplate", back_populates="created_by_user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
