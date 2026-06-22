from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from uuid import UUID

class PlanExercise(BaseModel):
    exercise_name: str
    sets: int
    reps: int
    target_rest_seconds: int
    muscles_targeted: List[str]
    estimated_calories: int

class PlanCreate(BaseModel):
    goal: str  # "Muscle Gain", "Weight Loss", "Strength", "Endurance"

class PlanRead(BaseModel):
    name: str
    goal: str
    description: str
    estimated_duration_minutes: int
    estimated_calories_burned: int
    exercises: List[PlanExercise]
