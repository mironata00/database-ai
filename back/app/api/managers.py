from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.core.security import security
from app.models.user import User, UserRole
from app.api.auth import oauth2_scheme

router = APIRouter()


async def get_current_admin_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    payload = security.decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administrators can access this resource")
    return user


@router.get("/")
async def get_users(
    role: Optional[str] = Query(None), search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None), skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100), current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(User)
    if role:
        try:
            role_enum = UserRole(role)
            query = query.where(User.role == role_enum)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid role")
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    if search:
        search_filter = f"%{search}%"
        query = query.where((User.email.ilike(search_filter)) | (User.full_name.ilike(search_filter)))
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()
    return {
        "users": [{"id": str(u.id), "email": u.email, "full_name": u.full_name, "role": u.role.value,
                  "is_active": u.is_active, "created_at": u.created_at.isoformat() if u.created_at else None,
                  "updated_at": u.updated_at.isoformat() if u.updated_at else None} for u in users],
        "total": total, "skip": skip, "limit": limit
    }


@router.get("/{user_id}")
async def get_user(user_id: UUID, current_user: User = Depends(get_current_admin_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"id": str(user.id), "email": user.email, "full_name": user.full_name, "role": user.role.value,
            "is_active": user.is_active, "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None}


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(email: str, password: str, full_name: Optional[str] = None, role: str = "manager",
                     is_active: bool = True, current_user: User = Depends(get_current_admin_user),
                     db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email already exists")
    try:
        role_enum = UserRole(role)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    hashed_password = security.hash_password(password)
    new_user = User(email=email, hashed_password=hashed_password, full_name=full_name, role=role_enum, is_active=is_active)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return {"id": str(new_user.id), "email": new_user.email, "full_name": new_user.full_name,
            "role": new_user.role.value, "is_active": new_user.is_active,
            "created_at": new_user.created_at.isoformat() if new_user.created_at else None}


@router.patch("/{user_id}")
async def update_user(user_id: UUID, email: Optional[str] = None, full_name: Optional[str] = None,
                     role: Optional[str] = None, is_active: Optional[bool] = None,
                     current_user: User = Depends(get_current_admin_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == current_user.id:
        if role is not None and role != user.role.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot change your own role")
        if is_active is not None and not is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot deactivate yourself")
    if email is not None and email != user.email:
        result = await db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
        user.email = email
    if full_name is not None:
        user.full_name = full_name
    if role is not None:
        try:
            user.role = UserRole(role)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    if is_active is not None:
        user.is_active = is_active
    await db.commit()
    await db.refresh(user)
    return {"id": str(user.id), "email": user.email, "full_name": user.full_name, "role": user.role.value,
            "is_active": user.is_active, "updated_at": user.updated_at.isoformat() if user.updated_at else None}


@router.patch("/{user_id}/password")
async def update_user_password(user_id: UUID, new_password: str, current_user: User = Depends(get_current_admin_user),
                               db: AsyncSession = Depends(get_db)):
    if len(new_password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.hashed_password = security.hash_password(new_password)
    await db.commit()
    return {"message": "Password updated successfully", "user_id": str(user.id)}


@router.delete("/{user_id}")
async def delete_user(user_id: UUID, current_user: User = Depends(get_current_admin_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delete yourself")
    await db.delete(user)
    await db.commit()
    return {"message": "User deleted successfully", "user_id": str(user_id)}
