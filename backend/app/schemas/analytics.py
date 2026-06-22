from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import date

class DailySummary(BaseModel):
    date: date
    total_reps: int
    total_duration_seconds: int
    total_calories: int
    average_form_score: float
    exercises_done: List[str]

class WeeklySummary(BaseModel):
    week_start: date
    total_reps: int
    total_duration_seconds: int
    total_calories: int
    average_form_score: float
    daily_breakdown: List[Dict[str, Any]]

class PerformanceMetric(BaseModel):
    exercise_name: str
    reps_count: int
    average_form_score: float
    average_duration_ms: float
    muscle_activation: Dict[str, float]
