import uuid
from sqlalchemy import Column, DateTime, ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func

from app.db.base import Base


class PoseFrame(Base):
    __tablename__ = "pose_frames"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    frame_id = Column(String, nullable=True)
    ts = Column(DateTime(timezone=True), nullable=False)
    landmarks = Column(JSON, nullable=True)
    source = Column(String, nullable=True)
