import uuid
from sqlalchemy import Column, String, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.db.base import Base


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    default_reps = Column(Integer, nullable=True)
    template = Column(JSON, nullable=True)
