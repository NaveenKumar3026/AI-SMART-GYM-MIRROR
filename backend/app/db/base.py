from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import models here for Alembic autogenerate
from app.models import user, session as session_model, exercise, rep, pose_frame, form_issue  # noqa: F401
