from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.session_service import SessionService
from app.api.v1.auth import get_current_user
from app.schemas.user import UserRead
from app.schemas.plans import PlanCreate, PlanRead
from ai_engine.workout_recommendation.recommender import WorkoutRecommender

router = APIRouter()

# In-memory template base for default templates
TEMPLATES = [
    {
        "name": "Hypertrophy Push-Pull-Legs",
        "goal": "Muscle Gain",
        "description": "Standard hypertrophy split balancing upper body press, pull, and lower body.",
        "estimated_duration_minutes": 45,
        "estimated_calories_burned": 350,
        "exercises": [
            {"exercise_name": "Squat", "sets": 3, "reps": 10, "target_rest_seconds": 60, "muscles_targeted": ["quadriceps", "gluteus_maximus"], "estimated_calories": 90},
            {"exercise_name": "Bench Press", "sets": 3, "reps": 10, "target_rest_seconds": 60, "muscles_targeted": ["chest", "triceps"], "estimated_calories": 70},
            {"exercise_name": "Pull-up", "sets": 3, "reps": 8, "target_rest_seconds": 90, "muscles_targeted": ["lats", "biceps"], "estimated_calories": 80},
            {"exercise_name": "Bicep Curl", "sets": 3, "reps": 12, "target_rest_seconds": 45, "muscles_targeted": ["biceps"], "estimated_calories": 40}
        ]
    },
    {
        "name": "Fat Burner Circuit",
        "goal": "Weight Loss",
        "description": "A high-intensity, short-rest circuit designed to elevate heart rate and maximize calorie spend.",
        "estimated_duration_minutes": 30,
        "estimated_calories_burned": 400,
        "exercises": [
            {"exercise_name": "Lunges", "sets": 3, "reps": 15, "target_rest_seconds": 30, "muscles_targeted": ["quadriceps", "glutes"], "estimated_calories": 80},
            {"exercise_name": "Push-up", "sets": 3, "reps": 15, "target_rest_seconds": 30, "muscles_targeted": ["chest", "triceps"], "estimated_calories": 75},
            {"exercise_name": "Squat", "sets": 3, "reps": 15, "target_rest_seconds": 30, "muscles_targeted": ["quadriceps"], "estimated_calories": 90},
            {"exercise_name": "Lunges", "sets": 3, "reps": 15, "target_rest_seconds": 30, "muscles_targeted": ["gluteus_maximus", "calves"], "estimated_calories": 80}
        ]
    }
]

@router.get("/plans")
async def get_plans(current_user: UserRead = Depends(get_current_user)):
    """
    Returns default template workouts.
    """
    return TEMPLATES

@router.post("/plans/generate", response_model=PlanRead)
async def generate_custom_plan(
    payload: PlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """
    Triggers the recommendation engine based on user goals and workout history.
    """
    session_service = SessionService(db)
    sessions = await session_service.get_user_sessions(current_user.id)
    
    # Process history
    history = []
    for s in sessions:
        if s.summary and isinstance(s.summary, dict):
            history.append({
                "exercise_name": s.summary.get("exercise")
            })

    recommender = WorkoutRecommender()
    recommendation = recommender.recommend(goal=payload.goal, history=history)
    return recommendation
