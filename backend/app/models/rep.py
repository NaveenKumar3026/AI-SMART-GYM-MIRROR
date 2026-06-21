import uuid
from sqlalchemy import Column, Integer, DateTime, ForeignKey, JSON, Float
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func

from app.db.base import Base


class Rep(Base):
    __tablename__ = "reps"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    rep_index = Column(Integer, nullable=False)
    start_ts = Column(DateTime(timezone=True), nullable=False)
    end_ts = Column(DateTime(timezone=True), nullable=False)
    duration_ms = Column(Integer, nullable=True)
    quality = Column(Float, nullable=True)
    metrics = Column(JSON, nullable=True)
