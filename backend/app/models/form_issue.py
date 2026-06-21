import uuid
from sqlalchemy import Column, DateTime, ForeignKey, String, Float, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func

from app.db.base import Base


class FormIssue(Base):
    __tablename__ = "form_issues"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    rep_id = Column(PGUUID(as_uuid=True), ForeignKey("reps.id"), nullable=True)
    code = Column(String, nullable=False)
    joint = Column(String, nullable=True)
    severity = Column(String, nullable=True)
    score = Column(Float, nullable=True)
    suggestion = Column(Text, nullable=True)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
