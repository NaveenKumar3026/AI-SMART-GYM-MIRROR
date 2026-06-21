from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.schemas.session import SessionCreate, SessionRead
from app.db.session import get_db
from app.services.session_service import SessionService

router = APIRouter()


@router.post("/sessions", response_model=SessionRead)
async def create_session(payload: SessionCreate, db: AsyncSession = Depends(get_db)):
    service = SessionService(db)
    session = await service.create_session(payload)
    return session


@router.patch("/sessions/{session_id}", response_model=SessionRead)
async def update_session(session_id: UUID, payload: dict, db: AsyncSession = Depends(get_db)):
    service = SessionService(db)
    session = await service.update_session(session_id, payload)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session
