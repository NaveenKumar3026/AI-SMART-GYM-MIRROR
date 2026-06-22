import time
from typing import Dict, Tuple, Any, Optional
from ai_engine.pose_detection.pose import extract_angles

class RepCounter:
    def __init__(self):
        self.reset()

    def reset(self):
        self.current_exercise = "unknown"
        self.reps = 0
        self.sets = 0
        
        # State machine variables
        self.state = "UP"  # UP, DOWN, GOING_UP, GOING_DOWN
        self.state_entered_time = time.time()
        
        # Tempo tracking
        self.eccentric_start_time = None
        self.pause_start_time = None
        self.concentric_start_time = None
        
        self.eccentric_duration = 0.0
        self.pause_duration = 0.0
        self.concentric_duration = 0.0
        
        self.last_rep_tempo = "0-0-0"
        self.last_rep_duration = 0.0
        self.rep_start_time = None

    def update(self, exercise: str, landmarks: list) -> Dict[str, Any]:
        """
        Processes a new frame's landmarks, runs the state machine, and returns counts/tempo.
        """
        if not landmarks or len(landmarks) < 33:
            return self.get_status()

        # If the exercise changed, reset the state machine for the new exercise
        if exercise != self.current_exercise and exercise != "unknown":
            self.reset()
            self.current_exercise = exercise
            # Set appropriate initial state based on exercise
            if exercise in ["Pull-up", "Deadlift", "Shoulder Press", "Bicep Curl", "Lunges"]:
                self.state = "DOWN"
            else:
                self.state = "UP"
            self.state_entered_time = time.time()

        angles = extract_angles(landmarks)
        if not angles:
            return self.get_status()

        # Joint configurations
        l_knee = angles.get("left_knee", 180.0)
        r_knee = angles.get("right_knee", 180.0)
        avg_knee = (l_knee + r_knee) / 2.0

        l_hip = angles.get("left_hip", 180.0)
        r_hip = angles.get("right_hip", 180.0)
        avg_hip = (l_hip + r_hip) / 2.0

        l_elbow = angles.get("left_elbow", 180.0)
        r_elbow = angles.get("right_elbow", 180.0)
        avg_elbow = (l_elbow + r_elbow) / 2.0

        # Execute state machine
        now = time.time()
        rep_completed = False

        if self.current_exercise == "Squat":
            # Standing = UP (knees extended > 160)
            # Squat bottom = DOWN (knees bent < 100)
            if self.state == "UP":
                if avg_knee < 155:
                    self.state = "GOING_DOWN"
                    self.eccentric_start_time = now
                    self.rep_start_time = now
            elif self.state == "GOING_DOWN":
                if avg_knee < 100:
                    self.state = "DOWN"
                    self.pause_start_time = now
                    if self.eccentric_start_time:
                        self.eccentric_duration = now - self.eccentric_start_time
                elif avg_knee > 160: # Aborted rep
                    self.state = "UP"
            elif self.state == "DOWN":
                if avg_knee > 105:
                    self.state = "GOING_UP"
                    self.concentric_start_time = now
                    if self.pause_start_time:
                        self.pause_duration = now - self.pause_start_time
                elif avg_knee > 160: # Fast recovery
                    self.state = "UP"
            elif self.state == "GOING_UP":
                if avg_knee > 160:
                    self.state = "UP"
                    if self.concentric_start_time:
                        self.concentric_duration = now - self.concentric_start_time
                    rep_completed = True

        elif self.current_exercise in ["Push-up", "Bench Press"]:
            # Arms locked = UP (elbows > 150)
            # Chest down = DOWN (elbows < 100)
            if self.state == "UP":
                if avg_elbow < 145:
                    self.state = "GOING_DOWN"
                    self.eccentric_start_time = now
                    self.rep_start_time = now
            elif self.state == "GOING_DOWN":
                if avg_elbow < 100:
                    self.state = "DOWN"
                    self.pause_start_time = now
                    if self.eccentric_start_time:
                        self.eccentric_duration = now - self.eccentric_start_time
                elif avg_elbow > 150:
                    self.state = "UP"
            elif self.state == "DOWN":
                if avg_elbow > 105:
                    self.state = "GOING_UP"
                    self.concentric_start_time = now
                    if self.pause_start_time:
                        self.pause_duration = now - self.pause_start_time
            elif self.state == "GOING_UP":
                if avg_elbow > 150:
                    self.state = "UP"
                    if self.concentric_start_time:
                        self.concentric_duration = now - self.concentric_start_time
                    rep_completed = True

        elif self.current_exercise in ["Bicep Curl", "Shoulder Press", "Pull-up"]:
            # Fully extended arms = DOWN (elbows > 150)
            # Peak flexion = UP (elbows < 80 for curl/pull-up, < 90 for shoulder press)
            threshold_peak = 90.0 if self.current_exercise == "Shoulder Press" else 80.0
            
            if self.state == "DOWN":
                if avg_elbow < 140:
                    self.state = "GOING_UP"
                    self.concentric_start_time = now
                    self.rep_start_time = now
            elif self.state == "GOING_UP":
                if avg_elbow < threshold_peak:
                    self.state = "UP"
                    self.pause_start_time = now
                    if self.concentric_start_time:
                        self.concentric_duration = now - self.concentric_start_time
                elif avg_elbow > 150:
                    self.state = "DOWN"
            elif self.state == "UP":
                if avg_elbow > (threshold_peak + 15):
                    self.state = "GOING_DOWN"
                    self.eccentric_start_time = now
                    if self.pause_start_time:
                        self.pause_duration = now - self.pause_start_time
            elif self.state == "GOING_DOWN":
                if avg_elbow > 150:
                    self.state = "DOWN"
                    if self.eccentric_start_time:
                        self.eccentric_duration = now - self.eccentric_start_time
                    rep_completed = True

        elif self.current_exercise == "Deadlift":
            # Hinging down = DOWN (hip angle < 120)
            # Lockout up = UP (hip angle > 160)
            if self.state == "DOWN":
                if avg_hip > 125:
                    self.state = "GOING_UP"
                    self.concentric_start_time = now
                    self.rep_start_time = now
            elif self.state == "GOING_UP":
                if avg_hip > 160:
                    self.state = "UP"
                    self.pause_start_time = now
                    if self.concentric_start_time:
                        self.concentric_duration = now - self.concentric_start_time
                elif avg_hip < 115:
                    self.state = "DOWN"
            elif self.state == "UP":
                if avg_hip < 150:
                    self.state = "GOING_DOWN"
                    self.eccentric_start_time = now
                    if self.pause_start_time:
                        self.pause_duration = now - self.pause_start_time
            elif self.state == "GOING_DOWN":
                if avg_hip < 115:
                    self.state = "DOWN"
                    if self.eccentric_start_time:
                        self.eccentric_duration = now - self.eccentric_start_time
                    rep_completed = True

        elif self.current_exercise == "Lunges":
            # Standing = UP (knees > 150)
            # Lunge bottom = DOWN (one knee < 105)
            min_knee = min(l_knee, r_knee)
            max_knee = max(l_knee, r_knee)
            
            if self.state == "UP":
                if min_knee < 140:
                    self.state = "GOING_DOWN"
                    self.eccentric_start_time = now
                    self.rep_start_time = now
            elif self.state == "GOING_DOWN":
                if min_knee < 105:
                    self.state = "DOWN"
                    self.pause_start_time = now
                    if self.eccentric_start_time:
                        self.eccentric_duration = now - self.eccentric_start_time
                elif min_knee > 150:
                    self.state = "UP"
            elif self.state == "DOWN":
                if min_knee > 115:
                    self.state = "GOING_UP"
                    self.concentric_start_time = now
                    if self.pause_start_time:
                        self.pause_duration = now - self.pause_start_time
            elif self.state == "GOING_UP":
                if min_knee > 150:
                    self.state = "UP"
                    if self.concentric_start_time:
                        self.concentric_duration = now - self.concentric_start_time
                    rep_completed = True

        if rep_completed:
            self.reps += 1
            if self.rep_start_time:
                self.last_rep_duration = now - self.rep_start_time
            # Format tempo: e.g. "3-0-1" (Eccentric-Pause-Concentric)
            self.last_rep_tempo = f"{round(self.eccentric_duration, 1)}s / {round(self.pause_duration, 1)}s / {round(self.concentric_duration, 1)}s"
            
            # Simple set progression: every 10 reps increases sets
            if self.reps > 0 and self.reps % 10 == 0:
                self.sets += 1
                
            # Clear durations
            self.eccentric_duration = 0.0
            self.pause_duration = 0.0
            self.concentric_duration = 0.0

        return self.get_status()

    def get_status(self) -> Dict[str, Any]:
        return {
            "exercise": self.current_exercise,
            "reps": self.reps,
            "sets": self.sets,
            "state": self.state,
            "tempo": self.last_rep_tempo,
            "duration": round(self.last_rep_duration, 2)
        }
