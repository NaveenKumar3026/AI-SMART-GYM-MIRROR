from pydantic import BaseModel
from typing import Optional

class CoachQuestion(BaseModel):
    question: str
    session_id: Optional[str] = None
    exercise: Optional[str] = None

class CoachResponse(BaseModel):
    response_text: str
    audio_url: Optional[str] = None  # Base64 data URI or file path containing synthesized speech
