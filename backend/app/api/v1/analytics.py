from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.session_service import SessionService
from app.api.v1.auth import get_current_user
from app.schemas.user import UserRead

router = APIRouter()

@router.get("/analytics/summary")
async def get_analytics_summary(
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    service = SessionService(db)
    summary = await service.get_analytics_summary(current_user.id)
    return summary
