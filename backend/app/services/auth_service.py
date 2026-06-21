from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta

from app.models.user import User
from app.schemas.auth import Token
from app.core.security import create_access_token
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str):
        res = await self.db.execute(select(User).where(User.email == email))
        return res.scalars().first()

    async def create_user(self, payload):
        hashed = pwd_context.hash(payload.password)
        user = User(email=payload.email, password_hash=hashed, display_name=payload.display_name)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def authenticate_and_get_token(self, email: str, password: str):
        user = await self.get_by_email(email)
        if not user:
            return None
        if not pwd_context.verify(password, user.password_hash):
            return None
        access_token = create_access_token(subject=str(user.id), expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
        return Token(access_token=access_token)
