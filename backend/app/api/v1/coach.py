from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.session_service import SessionService
from app.api.v1.auth import get_current_user
from app.schemas.user import UserRead
from app.schemas.coach import CoachQuestion, CoachResponse
from ai_engine.workout_recommendation.recommender import WorkoutRecommender
from ai_engine.muscle_mapper.mapper import MuscleMapper
import urllib.parse
from uuid import UUID

router = APIRouter()

@router.post("/coach/ask", response_model=CoachResponse)
async def ask_coach(
    payload: CoachQuestion,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """
    AI Coach responder supporting exercises, posture feedback, plan recommendations, and active muscle lookup.
    """
    question = payload.question.lower().strip()
    session_service = SessionService(db)

    # 1. Ask: "Am I doing this correctly?" or "How is my form?"
    if "correct" in question or "form" in question or "posture" in question:
        if not payload.session_id:
            text = "To check your form, please start a live workout session so I can observe your movements."
        else:
            try:
                s_id = UUID(payload.session_id)
                session_details = await session_service.get_session_details(s_id)
                issues = session_details.get("issues", [])
                score = session_details.get("average_form_score", 100.0)
                
                if not session_details:
                    text = "I couldn't find your current active session. Let's start a new workout."
                elif not issues:
                    text = f"Your form is looking solid! Your current score is {int(score)} percent. Keep maintaining neutral spine and controlled breathing."
                else:
                    issue_msg = issues[0]["suggestion"]
                    text = f"Your form score is {int(score)} percent. I noticed a small issue: {issue_msg} Focus on correcting this for your next rep."
            except Exception:
                text = "I ran into an issue pulling up your session data. Just keep your movements controlled and core tight."

    # 2. Ask: "What should I train next?" or "Recommend a workout"
    elif "next" in question or "recommend" in question or "train" in question or "workout plan" in question:
        sessions = await session_service.get_user_sessions(current_user.id)
        history = [{"exercise_name": s.summary.get("exercise")} for s in sessions if s.summary]
        
        # Decide goal
        goal = "Muscle Gain"
        if "lose" in question or "weight" in question or "burn" in question:
            goal = "Weight Loss"
        elif "strength" in question or "power" in question:
            goal = "Strength"
        elif "endurance" in question or "stamina" in question:
            goal = "Endurance"

        recommender = WorkoutRecommender()
        plan = recommender.recommend(goal=goal, history=history)
        ex_names = [e["exercise_name"] for e in plan["exercises"]]
        text = f"Based on your goal of {goal}, I recommend you train: {', '.join(ex_names)}. This routine focuses on {plan['description']}"

    # 3. Ask: "Which muscle is working?" or "What muscle does X train?"
    elif "muscle" in question or "work" in question or "activation" in question:
        exercise = payload.exercise or "Squat"
        # Determine if they named an exercise
        for ex in ["squat", "push-up", "bench press", "pull-up", "deadlift", "shoulder press", "bicep curl", "lunge"]:
            if ex in question:
                exercise = ex.title()
                break

        mapper = MuscleMapper()
        muscles = mapper.EXERCISE_MUSCLE_GROUPS.get(exercise, {})
        if muscles:
            primaries = [m.replace("_", " ") for m, cfg in muscles.items() if cfg["type"] == "primary"]
            secondaries = [m.replace("_", " ") for m, cfg in muscles.items() if cfg["type"] == "secondary"]
            text = f"During the {exercise}, your primary muscles working are the {', '.join(primaries)}."
            if secondaries:
                text += f" Secondary support comes from the {', '.join(secondaries)}."
        else:
            text = f"The active muscles depend on the movement. Let me know what exercise you are doing!"

    # 4. Ask: "Give me a chest workout"
    elif "chest" in question or "push" in question:
        text = "For chest, I recommend doing Bench Press or Push-ups. Perform 3 sets of 10 reps, maintaining controlled descent and tucking your elbows to protect your shoulders."

    # 5. Ask: "Give me a leg workout" or "lower body"
    elif "leg" in question or "quad" in question or "lower body" in question:
        text = "For your lower body, let's target Squats and Lunges. Execute 3 sets of 12 reps, driving through your heels and pushing your knees out."

    # Default fallback
    else:
        text = "I am your AI Mirror coach. You can ask me to check your form, recommend a custom workout routine, or tell you which muscles are active during your exercises!"

    # Simple dynamic speech synthesis URL generation
    # The client can read this text and play it via Web Speech API or hit a synthesis endpoint
    encoded_text = urllib.parse.quote(text)
    # We can point it to a speech endpoint, or let the frontend use window.speechSynthesis (responsive)
    audio_url = f"speak://?text={encoded_text}"

    return CoachResponse(
        response_text=text,
        audio_url=audio_url
    )
