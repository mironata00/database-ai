from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.viewer


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    
    # Провайдер почты
    email_provider_id: Optional[str] = None
    
    # SMTP поля
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: Optional[bool] = True
    smtp_from_name: Optional[str] = None
    
    # IMAP поля
    imap_host: Optional[str] = None
    imap_port: Optional[int] = 993
    imap_user: Optional[str] = None
    imap_password: Optional[str] = None
    imap_use_ssl: Optional[bool] = True
    
    # Email шаблоны
    email_default_subject: Optional[str] = "Запрос цен"
    email_default_body: Optional[str] = "Добрый день!\n\nПросим предоставить актуальные цены и сроки поставки на следующие товары:"
    email_signature: Optional[str] = "С уважением,"


class UserUpdate(BaseModel):
    """ТОЛЬКО админ может обновлять эти поля"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    
    # Провайдер почты
    email_provider_id: Optional[str] = None
    
    # SMTP настройки
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: Optional[bool] = None
    smtp_from_name: Optional[str] = None
    
    # IMAP настройки
    imap_host: Optional[str] = None
    imap_port: Optional[int] = None
    imap_user: Optional[str] = None
    imap_password: Optional[str] = None
    imap_use_ssl: Optional[bool] = None
    
    # Email шаблоны
    email_default_subject: Optional[str] = None
    email_default_body: Optional[str] = None
    email_signature: Optional[str] = None


class UserResponse(UserBase):
    id: str
    is_active: bool
    
    # Провайдер
    email_provider_id: Optional[str] = None
    
    # Показываем настроен ли SMTP/IMAP
    has_smtp_configured: bool = False
    has_imap_configured: bool = False
    has_email_configured: bool = False
    
    # SMTP данные (БЕЗ пароля)
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_from_name: Optional[str] = None
    smtp_use_tls: Optional[bool] = None
    
    # IMAP данные (БЕЗ пароля)
    imap_host: Optional[str] = None
    imap_port: Optional[int] = None
    imap_user: Optional[str] = None
    imap_use_ssl: Optional[bool] = None
    
    # Email шаблоны
    email_default_subject: Optional[str] = None
    email_default_body: Optional[str] = None
    email_signature: Optional[str] = None

    class Config:
        from_attributes = True
