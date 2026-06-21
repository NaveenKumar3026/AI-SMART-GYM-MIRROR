from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserCreate, UserRead
from app.schemas.auth import Token
from app.db.session import get_db
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserRead)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    existing = await service.get_by_email(payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = await service.create_user(payload)
    return user


@router.post("/login", response_model=Token)
async def login(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    token = await service.authenticate_and_get_token(payload.email, payload.password)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return token
