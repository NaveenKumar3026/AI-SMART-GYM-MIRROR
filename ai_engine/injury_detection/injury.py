from typing import Dict, List, Any
import time

class InjuryDetector:
    def __init__(self):
        self.angle_history = []
        self.time_history = []

    def detect_risk(self, exercise: str, landmarks: list, current_angles: dict) -> Dict[str, Any]:
        """
        Analyzes pose to detect risk of injury:
        - Hyperextension of knees/elbows (> 180 degrees)
        - Extreme spine flexion under load (Squat/Deadlift)
        - Loss of control (extreme speed/velocity of joint movement)
        """
        if not landmarks or len(landmarks) < 33 or not current_angles:
            return {"risk_level": "low", "warnings": []}

        warnings = []
        now = time.time()

        # Update historical cache (keep last 10 frames)
        self.angle_history.append(current_angles)
        self.time_history.append(now)
        if len(self.angle_history) > 10:
            self.angle_history.pop(0)
            self.time_history.pop(0)

        # 1. Hyperextension Check
        # Check knees
        l_knee = current_angles.get("left_knee", 180.0)
        r_knee = current_angles.get("right_knee", 180.0)
        if l_knee > 185.0 or r_knee > 185.0:
            warnings.append({
                "type": "HYPEREXTENSION",
                "joint": "Knee",
                "message": "Warning: Avoid locking out or hyperextending your knees."
            })

        # Check elbows
        l_elbow = current_angles.get("left_elbow", 180.0)
        r_elbow = current_angles.get("right_elbow", 180.0)
        if l_elbow > 185.0 or r_elbow > 185.0:
            warnings.append({
                "type": "HYPEREXTENSION",
                "joint": "Elbow",
                "message": "Warning: Avoid locking out or hyperextending your elbows."
            })

        # 2. Spinal flexion check during loaded movements
        spine_angle = current_angles.get("spine_angle", 0.0)
        if exercise in ["Deadlift", "Squat"] and spine_angle > 60.0:
            warnings.append({
                "type": "CRITICAL_SPINE_FLEXION",
                "joint": "Spine",
                "message": "DANGER: Severe back rounding! Stand up and reset posture immediately."
            })

        # 3. Velocity / Loss of control check (rapid drop)
        if len(self.angle_history) >= 3:
            # Measure rate of change of knee or elbow angles
            dt = self.time_history[-1] - self.time_history[-3]
            if dt > 0:
                if exercise in ["Squat", "Lunges"]:
                    dknee = self.angle_history[-3].get("left_knee", 180.0) - l_knee
                    knee_velocity = dknee / dt  # degrees per second
                    # If knee is bending faster than 180 deg/sec, it's a drop
                    if knee_velocity > 180.0:
                        warnings.append({
                            "type": "LOSS_OF_CONTROL",
                            "joint": "Knee",
                            "message": "Warning: Descending too fast. Control the eccentric phase."
                        })
                elif exercise in ["Push-up", "Bench Press"]:
                    delbow = self.angle_history[-3].get("left_elbow", 180.0) - l_elbow
                    elbow_velocity = delbow / dt
                    if elbow_velocity > 180.0:
                        warnings.append({
                            "type": "LOSS_OF_CONTROL",
                            "joint": "Elbow",
                            "message": "Warning: Control your descent. Don't drop under load."
                        })

        # Determine overall risk level
        risk_level = "low"
        for w in warnings:
            if w["type"] in ["CRITICAL_SPINE_FLEXION"]:
                risk_level = "high"
                break
            elif w["type"] in ["HYPEREXTENSION", "LOSS_OF_CONTROL"]:
                risk_level = "medium"

        return {
            "risk_level": risk_level,
            "warnings": warnings
        }
