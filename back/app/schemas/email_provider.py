from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class EmailProviderBase(BaseModel):
    """Базовая схема провайдера"""
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=255)
    
    # IMAP
    imap_host: str = Field(..., max_length=255)
    imap_port: int = Field(default=993, ge=1, le=65535)
    imap_use_ssl: bool = Field(default=True)
    
    # SMTP
    smtp_host: str = Field(..., max_length=255)
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_use_tls: bool = Field(default=True)
    
    description: Optional[str] = None
    is_active: bool = Field(default=True)


class EmailProviderCreate(EmailProviderBase):
    """Схема создания провайдера"""
    pass


class EmailProviderUpdate(BaseModel):
    """Схема обновления провайдера"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    
    imap_host: Optional[str] = Field(None, max_length=255)
    imap_port: Optional[int] = Field(None, ge=1, le=65535)
    imap_use_ssl: Optional[bool] = None
    
    smtp_host: Optional[str] = Field(None, max_length=255)
    smtp_port: Optional[int] = Field(None, ge=1, le=65535)
    smtp_use_tls: Optional[bool] = None
    
    description: Optional[str] = None
    is_active: Optional[bool] = None


class EmailProviderResponse(EmailProviderBase):
    """Схема ответа провайдера"""
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EmailProviderShort(BaseModel):
    """Краткая схема для выпадающего списка"""
    id: str
    name: str
    display_name: str
    
    # Настройки по умолчанию для автозаполнения
    imap_host: str
    imap_port: int
    imap_use_ssl: bool
    smtp_host: str
    smtp_port: int
    smtp_use_tls: bool

    class Config:
        from_attributes = True
