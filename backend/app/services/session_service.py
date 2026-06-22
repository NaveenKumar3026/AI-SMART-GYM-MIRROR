from sqlalchemy.ext.asyncio import AsyncSession
from app.models.session import Session
from app.models.rep import Rep
from app.models.form_issue import FormIssue
from app.models.pose_frame import PoseFrame
from app.models.exercise import Exercise
from app.schemas.session import SessionCreate
from sqlalchemy import insert, select, update, func, and_
from uuid import UUID
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional

class SessionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, payload: SessionCreate) -> Session:
        session = Session(
            user_id=payload.user_id,
            exercise_id=payload.exercise_id,
            status="active"
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_session(self, session_id: UUID) -> Optional[Session]:
        res = await self.db.execute(select(Session).where(Session.id == session_id))
        return res.scalars().first()

    async def get_user_sessions(self, user_id: UUID) -> List[Session]:
        res = await self.db.execute(
            select(Session)
            .where(Session.user_id == user_id)
            .order_by(Session.started_at.desc())
        )
        return list(res.scalars().all())

    async def update_session(self, session_id: UUID, payload: dict) -> Optional[Session]:
        stmt = update(Session).where(Session.id == session_id).values(**payload).returning(Session)
        res = await self.db.execute(stmt)
        await self.db.commit()
        row = res.fetchone()
        return row[0] if row else None

    async def add_rep(self, session_id: UUID, rep_index: int, start_ts: datetime, end_ts: datetime, duration_ms: int, quality: float, metrics: dict) -> Rep:
        rep = Rep(
            session_id=session_id,
            rep_index=rep_index,
            start_ts=start_ts,
            end_ts=end_ts,
            duration_ms=duration_ms,
            quality=quality,
            metrics=metrics
        )
        self.db.add(rep)
        await self.db.commit()
        await self.db.refresh(rep)
        return rep

    async def add_form_issue(self, session_id: UUID, code: str, joint: str, severity: str, score: float, suggestion: str, rep_id: Optional[UUID] = None) -> FormIssue:
        issue = FormIssue(
            session_id=session_id,
            rep_id=rep_id,
            code=code,
            joint=joint,
            severity=severity,
            score=score,
            suggestion=suggestion
        )
        self.db.add(issue)
        await self.db.commit()
        await self.db.refresh(issue)
        return issue

    async def add_pose_frame(self, session_id: UUID, frame_id: str, ts: datetime, landmarks: list, source: str) -> PoseFrame:
        frame = PoseFrame(
            session_id=session_id,
            frame_id=frame_id,
            ts=ts,
            landmarks=landmarks,
            source=source
        )
        self.db.add(frame)
        await self.db.commit()
        await self.db.refresh(frame)
        return frame

    async def get_session_details(self, session_id: UUID) -> Dict[str, Any]:
        """
        Gathers complete aggregates for a session (total reps, duration, issues, exercises).
        """
        session = await self.get_session(session_id)
        if not session:
            return {}

        # Query reps
        reps_res = await self.db.execute(select(Rep).where(Rep.session_id == session_id).order_by(Rep.rep_index.asc()))
        reps = reps_res.scalars().all()

        # Query issues
        issues_res = await self.db.execute(select(FormIssue).where(FormIssue.session_id == session_id))
        issues = issues_res.scalars().all()

        # Calculate durations
        duration = 0
        if session.ended_at and session.started_at:
            duration = int((session.ended_at - session.started_at).total_seconds())
        elif session.started_at:
            duration = int((datetime.utcnow() - session.started_at.replace(tzinfo=None)).total_seconds())

        # Calories estimation (approx 0.12 kcal per rep for compound movements)
        total_reps = len(reps)
        calories = int(total_reps * 7.5) # ~7.5 kcal per rep average

        # Compute average form score
        form_scores = [100.0 - (10.0 if issue.severity == "low" else 20.0 if issue.severity == "medium" else 40.0) for issue in issues]
        avg_score = sum(form_scores) / len(form_scores) if form_scores else 95.0
        avg_score = max(0.0, min(100.0, avg_score))

        return {
            "session_id": session_id,
            "status": session.status,
            "started_at": session.started_at,
            "ended_at": session.ended_at,
            "duration_seconds": duration,
            "total_reps": total_reps,
            "calories_burned": calories,
            "average_form_score": avg_score,
            "reps": [{
                "index": r.rep_index,
                "duration_ms": r.duration_ms,
                "quality": r.quality,
                "tempo": r.metrics.get("tempo", "") if r.metrics else ""
            } for r in reps],
            "issues": [{
                "code": i.code,
                "joint": i.joint,
                "severity": i.severity,
                "suggestion": i.suggestion
            } for i in issues]
        }

    async def get_analytics_summary(self, user_id: UUID) -> Dict[str, Any]:
        """
        Compiles analytical data across all sessions for this user over the past 30 days.
        """
        # Fetch sessions
        sessions = await self.get_user_sessions(user_id)
        if not sessions:
            return {
                "total_reps": 0,
                "total_duration_seconds": 0,
                "total_calories": 0,
                "average_form_score": 100.0,
                "daily_reports": []
            }

        total_reps = 0
        total_duration = 0
        total_calories = 0
        form_scores = []

        daily_map = {}

        # Loop through sessions
        for s in sessions:
            det = await self.get_session_details(s.id)
            if not det:
                continue

            total_reps += det["total_reps"]
            total_duration += det["duration_seconds"]
            total_calories += det["calories_burned"]
            form_scores.append(det["average_form_score"])

            # Group by day
            day_str = s.started_at.date().isoformat()
            if day_str not in daily_map:
                daily_map[day_str] = {
                    "date": day_str,
                    "reps": 0,
                    "duration": 0,
                    "calories": 0,
                    "form_scores": []
                }
            
            daily_map[day_str]["reps"] += det["total_reps"]
            daily_map[day_str]["duration"] += det["duration_seconds"]
            daily_map[day_str]["calories"] += det["calories_burned"]
            daily_map[day_str]["form_scores"].append(det["average_form_score"])

        # Formulate daily report array
        daily_reports = []
        for d_str, val in sorted(daily_map.items()):
            avg_fs = sum(val["form_scores"]) / len(val["form_scores"]) if val["form_scores"] else 100.0
            daily_reports.append({
                "date": val["date"],
                "total_reps": val["reps"],
                "total_duration_seconds": val["duration"],
                "total_calories": val["calories"],
                "average_form_score": round(avg_fs, 1)
            })

        avg_overall_score = sum(form_scores) / len(form_scores) if form_scores else 100.0

        return {
            "total_reps": total_reps,
            "total_duration_seconds": total_duration,
            "total_calories": total_calories,
            "average_form_score": round(avg_overall_score, 1),
            "daily_reports": daily_reports
        }
