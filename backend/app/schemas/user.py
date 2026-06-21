from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    display_name: Optional[str]


class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    display_name: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True
