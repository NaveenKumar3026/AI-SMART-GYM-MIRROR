from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class SessionCreate(BaseModel):
    user_id: Optional[UUID]
    exercise_id: Optional[UUID]
    device_id: Optional[UUID]
    mode: Optional[str] = "workout"


class SessionRead(BaseModel):
    id: UUID
    user_id: Optional[UUID]
    exercise_id: Optional[UUID]
    status: str
    started_at: datetime
    ended_at: Optional[datetime]
    summary: Optional[dict]

    class Config:
        orm_mode = True
