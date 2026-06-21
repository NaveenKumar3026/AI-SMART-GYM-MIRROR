from sqlalchemy.ext.asyncio import AsyncSession
from app.models.session import Session
from app.schemas.session import SessionCreate
from sqlalchemy import insert, select, update
from uuid import UUID


class SessionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, payload: SessionCreate):
        stmt = insert(Session).values(
            user_id=payload.user_id,
            exercise_id=payload.exercise_id,
            status="active",
        ).returning(Session)
        res = await self.db.execute(stmt)
        await self.db.commit()
        session = res.fetchone()[0]
        return session

    async def update_session(self, session_id: UUID, payload: dict):
        stmt = update(Session).where(Session.id == session_id).values(**payload).returning(Session)
        res = await self.db.execute(stmt)
        await self.db.commit()
        row = res.fetchone()
        return row[0] if row else None
