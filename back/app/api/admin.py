from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

router = APIRouter()

@router.get("/pending-imports")
async def get_pending_imports(db: AsyncSession = Depends(get_db)):
    return {"message": "Pending imports endpoint - implementation in progress"}

@router.post("/pending-imports/{import_id}/approve")
async def approve_import(import_id: str, db: AsyncSession = Depends(get_db)):
    return {"message": f"Approving import {import_id}"}
