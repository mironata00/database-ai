from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.core.security import security
from app.api.auth import get_current_user

router = APIRouter()

def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user

@router.post("/", response_model=UserResponse)
async def create_manager(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(
        email=user_data.email,
        hashed_password=security.get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        is_active=user_data.is_active if hasattr(user_data, 'is_active') else True,
        smtp_host=user_data.smtp_host,
        smtp_port=user_data.smtp_port or 587,
        smtp_user=user_data.smtp_user,
        smtp_password=user_data.smtp_password,
        smtp_use_tls=user_data.smtp_use_tls if hasattr(user_data, 'smtp_use_tls') else True,
        smtp_from_name=user_data.smtp_from_name,
        email_default_subject=user_data.email_default_subject or "Запрос цен",
        email_default_body=user_data.email_default_body or "Добрый день!\n\nПросим предоставить актуальные цены и сроки поставки на следующие товары:",
        email_signature=user_data.email_signature or "С уважением,"
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return UserResponse(
        id=str(new_user.id),
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role,
        is_active=new_user.is_active,
        has_smtp_configured=new_user.has_smtp_configured(),
        smtp_host=new_user.smtp_host,
        smtp_port=new_user.smtp_port,
        smtp_user=new_user.smtp_user,
        smtp_from_name=new_user.smtp_from_name,
        email_default_subject=new_user.email_default_subject,
        email_default_body=new_user.email_default_body,
        email_signature=new_user.email_signature
    )

@router.get("/", response_model=List[UserResponse])
async def list_managers(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    result = await db.execute(
        select(User).where(User.role.in_([UserRole.manager, UserRole.admin])).limit(limit)
    )
    users = result.scalars().all()
    
    return [
        UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            has_smtp_configured=user.has_smtp_configured(),
            smtp_host=user.smtp_host,
            smtp_port=user.smtp_port,
            smtp_user=user.smtp_user,
            smtp_from_name=user.smtp_from_name,
            email_default_subject=user.email_default_subject,
            email_default_body=user.email_default_body,
            email_signature=user.email_signature
        )
        for user in users
    ]

@router.get("/{user_id}", response_model=UserResponse)
async def get_manager(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        has_smtp_configured=user.has_smtp_configured(),
        smtp_host=user.smtp_host,
        smtp_port=user.smtp_port,
        smtp_user=user.smtp_user,
        smtp_from_name=user.smtp_from_name,
        email_default_subject=user.email_default_subject,
        email_default_body=user.email_default_body,
        email_signature=user.email_signature
    )

# PATCH для обновления
@router.patch("/{user_id}", response_model=UserResponse)
async def update_manager_patch(
    user_id: str,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    return await _update_manager(user_id, user_data, db)

# PUT для обновления (тот же код)
@router.put("/{user_id}", response_model=UserResponse)
async def update_manager_put(
    user_id: str,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    return await _update_manager(user_id, user_data, db)

async def _update_manager(user_id: str, user_data: UserUpdate, db: AsyncSession):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_data.model_dump(exclude_unset=True)
    
    if "password" in update_data:
        update_data["hashed_password"] = security.get_password_hash(update_data.pop("password"))
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        has_smtp_configured=user.has_smtp_configured(),
        smtp_host=user.smtp_host,
        smtp_port=user.smtp_port,
        smtp_user=user.smtp_user,
        smtp_from_name=user.smtp_from_name,
        email_default_subject=user.email_default_subject,
        email_default_body=user.email_default_body,
        email_signature=user.email_signature
    )

@router.delete("/{user_id}")
async def delete_manager(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.delete(user)
    await db.commit()
    
    return {"success": True}
