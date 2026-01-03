from sqlalchemy import Column, String, Integer, Boolean, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class EmailProvider(BaseModel):
    """Модель почтового провайдера (хостера)"""
    __tablename__ = "email_providers"

    # Идентификация
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    
    # IMAP настройки
    imap_host = Column(String(255), nullable=False)
    imap_port = Column(Integer, nullable=False, default=993)
    imap_use_ssl = Column(Boolean, nullable=False, default=True)
    
    # SMTP настройки
    smtp_host = Column(String(255), nullable=False)
    smtp_port = Column(Integer, nullable=False, default=587)
    smtp_use_tls = Column(Boolean, nullable=False, default=True)
    
    # Метаданные
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    users = relationship("User", back_populates="email_provider")

    def __repr__(self):
        return f"<EmailProvider {self.name} ({self.display_name})>"
