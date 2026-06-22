from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.websocket.manager import manager
from app.core.security import decode_token
from app.db.session import async_session
from app.services.session_service import SessionService

# Import AI Engine
from ai_engine.pose_detection.pose import extract_angles
from ai_engine.exercise_recognition.classifier import ExerciseClassifier
from ai_engine.rep_counter.rep_counter import RepCounter
from ai_engine.form_analysis.form_analyzer import FormAnalyzer
from ai_engine.muscle_mapper.mapper import MuscleMapper
from ai_engine.injury_detection.injury import InjuryDetector

from uuid import UUID
from datetime import datetime
import json
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    payload = decode_token(token) if token else None
    
    # Allow free access for testing if no token provided, using query parameter session_id
    param_session_id = websocket.query_params.get("session_id")
    session_id_str = param_session_id or (payload and payload.get("sub"))
    
    if not session_id_str:
        await websocket.close(code=4001)
        return

    try:
        session_id = UUID(session_id_str)
    except ValueError:
        # If not a valid UUID, just generate or use fake for demo
        try:
            import uuid
            session_id = uuid.uuid4()
            session_id_str = str(session_id)
        except Exception:
            await websocket.close(code=4002)
            return

    await manager.connect(session_id_str, websocket)

    # Instantiate AI trackers for this socket session
    classifier = ExerciseClassifier()
    rep_counter = RepCounter()
    form_analyzer = FormAnalyzer()
    muscle_mapper = MuscleMapper()
    injury_detector = InjuryDetector()

    # Track rep index locally to detect new reps
    last_rep_count = 0

    try:
        # Verify/initialize the session in the DB
        async with async_session() as db:
            session_service = SessionService(db)
            db_session = await session_service.get_session(session_id)
            if not db_session:
                # If session doesn't exist yet, we can create it dynamically
                from app.schemas.session import SessionCreate
                await session_service.create_session(SessionCreate(
                    user_id=None,
                    exercise_id=None,
                    device_id=None
                ))

        while True:
            # Receive frame landmarks
            data = await websocket.receive_json()
            
            # Allow control message for ending session early
            if data.get("type") == "end_session":
                async with async_session() as db:
                    session_service = SessionService(db)
                    agg = await session_service.get_session_details(session_id)
                    await session_service.update_session(session_id, {
                        "status": "completed",
                        "ended_at": datetime.utcnow(),
                        "summary": {
                            "exercise": rep_counter.current_exercise,
                            "reps": rep_counter.reps,
                            "sets": rep_counter.sets,
                            "average_form_score": agg.get("average_form_score", 95.0),
                            "duration_seconds": agg.get("duration_seconds", 0),
                            "calories_burned": agg.get("calories_burned", 0)
                        }
                    })
                await websocket.send_json({"type": "session_completed", "summary": agg})
                break

            landmarks = data.get("landmarks")
            if not landmarks or len(landmarks) < 33:
                continue

            # 1. Pose Feature & Angles extraction
            angles = extract_angles(landmarks)
            
            # 2. Exercise recognition (fallback if not explicitly specified by client)
            client_exercise = data.get("exercise")
            if client_exercise and client_exercise != "unknown":
                exercise = client_exercise
                confidence = 1.0
            else:
                exercise, confidence = classifier.classify(landmarks)

            # 3. Process states if exercise is recognized
            rep_status = {"reps": 0, "sets": 0, "state": "UP", "tempo": "0-0-0", "duration": 0.0}
            form_res = {"form_score": 100, "issues": [], "feedback": "Aligning skeleton..."}
            muscle_activation = {}
            injury_res = {"risk_level": "low", "warnings": []}

            if exercise != "unknown":
                # State-machine rep count
                rep_status = rep_counter.update(exercise, landmarks)
                
                # Biomechanical form correction
                form_res = form_analyzer.analyze(exercise, landmarks, rep_status["state"])
                
                # Active muscles intensity
                muscle_activation = muscle_mapper.get_activation(exercise, landmarks)
                
                # Sudden falls/strain detection
                injury_res = injury_detector.detect_risk(exercise, landmarks, angles)

            # 4. Persistence into Database
            # We record a subset of frames to database to avoid overflow
            frame_id = data.get("frame_id") or str(int(datetime.utcnow().timestamp() * 1000))
            frame_ts = datetime.utcnow()
            
            async with async_session() as db:
                session_service = SessionService(db)
                
                # Persist raw frame (e.g. sample every 5th frame, or if issues detected)
                if int(frame_id) % 5 == 0 or len(form_res["issues"]) > 0:
                    await session_service.add_pose_frame(
                        session_id=session_id,
                        frame_id=frame_id,
                        ts=frame_ts,
                        landmarks=landmarks,
                        source=data.get("source", "webcam")
                    )

                # Check if a new rep has been completed
                current_reps = rep_status["reps"]
                if current_reps > last_rep_count:
                    # Save completed rep
                    duration_ms = int(rep_status["duration"] * 1000)
                    rep_record = await session_service.add_rep(
                        session_id=session_id,
                        rep_index=current_reps,
                        start_ts=datetime.utcnow(),  # approximation
                        end_ts=datetime.utcnow(),
                        duration_ms=duration_ms,
                        quality=float(form_res["form_score"]) / 100.0,
                        metrics={"tempo": rep_status["tempo"]}
                    )
                    
                    # Save form issues associated with this rep
                    for issue in form_res["issues"]:
                        await session_service.add_form_issue(
                            session_id=session_id,
                            rep_id=rep_record.id,
                            code=issue["code"],
                            joint=issue["joint"],
                            severity=issue["severity"],
                            score=float(issue["score"]),
                            suggestion=issue["suggestion"]
                        )
                    
                    last_rep_count = current_reps

                # If injury risks are identified, save them
                for warning in injury_res["warnings"]:
                    await session_service.add_form_issue(
                        session_id=session_id,
                        rep_id=None,
                        code=warning["type"],
                        joint=warning["joint"],
                        severity="high" if injury_res["risk_level"] == "high" else "medium",
                        score=50.0,
                        suggestion=warning["message"]
                    )

            # 5. Broadcast real-time feedback to client
            feedback_payload = {
                "type": "pose_feedback",
                "exercise": exercise,
                "confidence": confidence,
                "reps": rep_status["reps"],
                "sets": rep_status["sets"],
                "state": rep_status["state"],
                "tempo": rep_status["tempo"],
                "form_score": form_res["form_score"],
                "feedback": form_res["feedback"],
                "muscles": muscle_activation,
                "injury_risk": injury_res["risk_level"],
                "injury_warnings": [w["message"] for w in injury_res["warnings"]],
                "landmarks": landmarks
            }
            await manager.broadcast(session_id_str, feedback_payload)

    except WebSocketDisconnect:
        await manager.disconnect(session_id_str, websocket)
        # Finalize the session stats
        async with async_session() as db:
            session_service = SessionService(db)
            agg = await session_service.get_session_details(session_id)
            if agg:
                await session_service.update_session(session_id, {
                    "status": "completed",
                    "ended_at": datetime.utcnow(),
                    "summary": {
                        "exercise": rep_counter.current_exercise,
                        "reps": rep_counter.reps,
                        "sets": rep_counter.sets,
                        "average_form_score": agg.get("average_form_score", 95.0),
                        "duration_seconds": agg.get("duration_seconds", 0),
                        "calories_burned": agg.get("calories_burned", 0)
                    }
                })
        logger.info(f"WebSocket session {session_id_str} disconnected and finalized.")
