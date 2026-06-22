from typing import Dict
from ai_engine.pose_detection.pose import extract_angles

class MuscleMapper:
    # Static database of exercise muscle mappings
    EXERCISE_MUSCLE_GROUPS = {
        "Squat": {
            "quadriceps": {"type": "primary", "base": 0.4},
            "gluteus_maximus": {"type": "primary", "base": 0.3},
            "hamstrings": {"type": "secondary", "base": 0.2},
            "calves": {"type": "secondary", "base": 0.1},
            "core": {"type": "secondary", "base": 0.1}
        },
        "Push-up": {
            "chest": {"type": "primary", "base": 0.5},
            "triceps": {"type": "primary", "base": 0.3},
            "front_deltoids": {"type": "secondary", "base": 0.15},
            "core": {"type": "secondary", "base": 0.1}
        },
        "Bench Press": {
            "chest": {"type": "primary", "base": 0.6},
            "triceps": {"type": "primary", "base": 0.25},
            "front_deltoids": {"type": "secondary", "base": 0.15}
        },
        "Pull-up": {
            "lats": {"type": "primary", "base": 0.5},
            "biceps": {"type": "primary", "base": 0.3},
            "upper_back": {"type": "secondary", "base": 0.15},
            "core": {"type": "secondary", "base": 0.1}
        },
        "Deadlift": {
            "hamstrings": {"type": "primary", "base": 0.35},
            "gluteus_maximus": {"type": "primary", "base": 0.3},
            "lower_back": {"type": "primary", "base": 0.2},
            "forearms": {"type": "secondary", "base": 0.1},
            "traps": {"type": "secondary", "base": 0.1}
        },
        "Shoulder Press": {
            "shoulders": {"type": "primary", "base": 0.6},
            "triceps": {"type": "primary", "base": 0.25},
            "upper_chest": {"type": "secondary", "base": 0.1},
            "core": {"type": "secondary", "base": 0.1}
        },
        "Bicep Curl": {
            "biceps": {"type": "primary", "base": 0.8},
            "forearms": {"type": "secondary", "base": 0.15},
            "brachialis": {"type": "secondary", "base": 0.1}
        },
        "Lunges": {
            "quadriceps": {"type": "primary", "base": 0.45},
            "gluteus_maximus": {"type": "primary", "base": 0.35},
            "calves": {"type": "secondary", "base": 0.1},
            "hamstrings": {"type": "secondary", "base": 0.1}
        }
    }

    def get_activation(self, exercise: str, landmarks: list) -> Dict[str, float]:
        """
        Calculates dynamic muscle activation levels (0.0 to 1.0) based on joint flexion.
        As a user descends in a squat, the activation increases.
        """
        if exercise not in self.EXERCISE_MUSCLE_GROUPS:
            return {}

        angles = extract_angles(landmarks)
        if not angles:
            # Return baseline values if no pose is extracted
            return {muscle: float(cfg["base"]) for muscle, cfg in self.EXERCISE_MUSCLE_GROUPS[exercise].items()}

        muscle_map = self.EXERCISE_MUSCLE_GROUPS[exercise]
        activation = {}

        # We can scale the activation based on exercise depth/flexion
        l_knee = angles.get("left_knee", 180.0)
        r_knee = angles.get("right_knee", 180.0)
        avg_knee = (l_knee + r_knee) / 2.0

        l_elbow = angles.get("left_elbow", 180.0)
        r_elbow = angles.get("right_elbow", 180.0)
        avg_elbow = (l_elbow + r_elbow) / 2.0

        l_hip = angles.get("left_hip", 180.0)
        r_hip = angles.get("right_hip", 180.0)
        avg_hip = (l_hip + r_hip) / 2.0

        # Scale factor (0.0 to 1.0) showing intensity/stretch of the movement
        intensity = 0.5  # default baseline scale

        if exercise == "Squat":
            # Deepest squat (knee angle ~90) has highest quad/glute activation
            intensity = max(0.2, min(1.0, (180.0 - avg_knee) / 90.0))
        elif exercise in ["Push-up", "Bench Press"]:
            # Bottom of press (elbow angle ~90) has highest chest/tricep activation
            intensity = max(0.2, min(1.0, (180.0 - avg_elbow) / 90.0))
        elif exercise in ["Pull-up", "Bicep Curl"]:
            # Peak contraction (elbow angle ~60) has highest bicep/lat activation
            intensity = max(0.2, min(1.0, (180.0 - avg_elbow) / 120.0))
        elif exercise == "Shoulder Press":
            intensity = max(0.2, min(1.0, (180.0 - avg_elbow) / 90.0))
        elif exercise == "Deadlift":
            # Hinging at bottom (hip angle ~100) stretches hamstrings/glutes
            intensity = max(0.2, min(1.0, (180.0 - avg_hip) / 80.0))
        elif exercise == "Lunges":
            min_knee = min(l_knee, r_knee)
            intensity = max(0.2, min(1.0, (180.0 - min_knee) / 85.0))

        # Populate activation levels
        for muscle, cfg in muscle_map.items():
            base = cfg["base"]
            is_primary = cfg["type"] == "primary"
            
            # Primary muscles scale higher with movement depth
            if is_primary:
                level = base + (1.0 - base) * intensity
            else:
                level = base + (0.5 - base) * intensity
                
            activation[muscle] = round(float(np.clip(level, 0.0, 1.0)), 2)

        return activation
