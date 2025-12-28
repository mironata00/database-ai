from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

router = APIRouter()

@router.get("/templates")
async def get_templates(db: AsyncSession = Depends(get_db)):
    return {"message": "Email templates endpoint"}

@router.post("/")
async def create_campaign(db: AsyncSession = Depends(get_db)):
    return {"message": "Create campaign endpoint"}
