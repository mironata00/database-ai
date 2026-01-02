from sqlalchemy import Column, String, Boolean, Enum as SQLEnum, Integer, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum

class UserRole(str, enum.Enum):
    admin = "admin"
    manager = "manager"
    viewer = "viewer"

class User(BaseModel):
    __tablename__ = "users"
    
    # Основные поля
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(
        SQLEnum(UserRole, name='user_role', create_type=False),
        nullable=False,
        default=UserRole.viewer
    )
    is_active = Column(Boolean, default=True, nullable=False)
    
    # SMTP настройки (управляются ТОЛЬКО админом)
    smtp_host = Column(String(255), nullable=True)
    smtp_port = Column(Integer, default=587, nullable=True)
    smtp_user = Column(String(255), nullable=True)
    smtp_password = Column(String(255), nullable=True)
    smtp_use_tls = Column(Boolean, default=True, nullable=True)
    smtp_from_name = Column(String(255), nullable=True)
    
    # Email шаблоны (управляются ТОЛЬКО админом)
    email_default_subject = Column(String(500), default='Запрос цен', nullable=True)
    email_default_body = Column(Text, default='Добрый день!\n\nПросим предоставить актуальные цены и сроки поставки на следующие товары:', nullable=True)
    email_signature = Column(Text, default='С уважением,', nullable=True)
    
    # Relationships
    ratings = relationship("Rating", back_populates="manager", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    email_campaigns = relationship("EmailCampaign", back_populates="created_by_user", cascade="all, delete-orphan")
    email_templates = relationship("EmailTemplate", back_populates="created_by_user", cascade="all, delete-orphan")
    
    def has_smtp_configured(self) -> bool:
        """Проверка что админ настроил SMTP для этого менеджера"""
        return bool(
            self.smtp_host and 
            self.smtp_user and 
            self.smtp_password
        )
    
    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
