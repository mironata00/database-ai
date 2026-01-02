from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from app.models.user import UserRole

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.viewer

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    # SMTP поля опциональны при создании
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: Optional[bool] = True
    smtp_from_name: Optional[str] = None
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
    # SMTP настройки
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: Optional[bool] = None
    smtp_from_name: Optional[str] = None
    # Email шаблоны
    email_default_subject: Optional[str] = None
    email_default_body: Optional[str] = None
    email_signature: Optional[str] = None

class UserResponse(UserBase):
    id: str
    is_active: bool
    # Показываем настроен ли SMTP
    has_smtp_configured: bool = False
    # SMTP данные (БЕЗ пароля)
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_from_name: Optional[str] = None
    # Email шаблоны
    email_default_subject: Optional[str] = None
    email_default_body: Optional[str] = None
    email_signature: Optional[str] = None
    
    class Config:
        from_attributes = True
