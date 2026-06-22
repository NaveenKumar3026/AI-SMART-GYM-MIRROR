from typing import Dict, Tuple, Any
from ai_engine.pose_detection.pose import extract_angles, get_landmark_coords

class ExerciseClassifier:
    def __init__(self):
        # We can store some historical states if needed for temporal smoothing
        self.history = []

    def classify(self, landmarks: list) -> Tuple[str, float]:
        """
        Classifies the exercise based on joint angles and landmark positions.
        Returns: (exercise_name, confidence_score)
        """
        if not landmarks or len(landmarks) < 33:
            return "unknown", 0.0

        angles = extract_angles(landmarks)
        if not angles:
            return "unknown", 0.0

        try:
            # Extract coordinates for spatial relations
            l_shoulder = get_landmark_coords(landmarks, "LEFT_SHOULDER")
            r_shoulder = get_landmark_coords(landmarks, "RIGHT_SHOULDER")
            l_hip = get_landmark_coords(landmarks, "LEFT_HIP")
            r_hip = get_landmark_coords(landmarks, "RIGHT_HIP")
            l_knee = get_landmark_coords(landmarks, "LEFT_KNEE")
            r_knee = get_landmark_coords(landmarks, "RIGHT_KNEE")
            l_ankle = get_landmark_coords(landmarks, "LEFT_ANKLE")
            r_ankle = get_landmark_coords(landmarks, "RIGHT_ANKLE")
            l_wrist = get_landmark_coords(landmarks, "LEFT_WRIST")
            r_wrist = get_landmark_coords(landmarks, "RIGHT_WRIST")
            l_elbow = get_landmark_coords(landmarks, "LEFT_ELBOW")
            r_elbow = get_landmark_coords(landmarks, "RIGHT_ELBOW")
            nose = get_landmark_coords(landmarks, "NOSE")

            # Basic features
            spine_angle = angles.get("spine_angle", 0.0)
            
            # Joint angles
            l_knee_angle = angles.get("left_knee", 180.0)
            r_knee_angle = angles.get("right_knee", 180.0)
            avg_knee_angle = (l_knee_angle + r_knee_angle) / 2.0

            l_hip_angle = angles.get("left_hip", 180.0)
            r_hip_angle = angles.get("right_hip", 180.0)
            avg_hip_angle = (l_hip_angle + r_hip_angle) / 2.0

            l_elbow_angle = angles.get("left_elbow", 180.0)
            r_elbow_angle = angles.get("right_elbow", 180.0)
            avg_elbow_angle = (l_elbow_angle + r_elbow_angle) / 2.0

            l_shoulder_angle = angles.get("left_shoulder", 0.0)
            r_shoulder_angle = angles.get("right_shoulder", 0.0)
            avg_shoulder_angle = (l_shoulder_angle + r_shoulder_angle) / 2.0

            # Vertical relation: in MediaPipe, y decreases upwards (head is smaller y, feet are larger y)
            is_horizontal = spine_angle > 45.0  # Horizontal spine (Push-up, Bench Press)
            is_vertical = spine_angle <= 45.0    # Vertical spine (Squat, Deadlift, Shoulder Press, Bicep Curl, Lunge, Pull-up)

            # Let's check candidate confidence scores
            scores = {}

            # 1. SQUAT
            # Upright trunk, knees flexing, hips flexing, ankles flexing
            if is_vertical:
                # Squat: both knees bending, hips bending, torso remains relatively vertical
                knee_score = max(0.0, min(1.0, (170.0 - avg_knee_angle) / 80.0))
                hip_score = max(0.0, min(1.0, (170.0 - avg_hip_angle) / 85.0))
                torso_score = max(0.0, min(1.0, (50.0 - spine_angle) / 30.0))
                
                # Double check symmetry to distinguish from Lunges
                asymmetry = abs(l_knee_angle - r_knee_angle)
                symmetry_score = max(0.0, min(1.0, (70.0 - asymmetry) / 50.0))
                
                # Wrists should be below head (not overhead like shoulder press or pull-up)
                wrist_height_score = 1.0 if l_wrist[1] > l_shoulder[1] and r_wrist[1] > r_shoulder[1] else 0.2
                
                scores["Squat"] = float(knee_score * hip_score * torso_score * symmetry_score * wrist_height_score)
            else:
                scores["Squat"] = 0.0

            # 2. PUSH-UP
            # Horizontal trunk, face down, elbows flexing/extending
            if is_horizontal:
                # Nose is generally below the shoulders/elbows or facing down in depth (z)
                # In MediaPipe, y goes down, so nose y should be close to or below shoulder y
                # (but since spine is horizontal, it is roughly level)
                # Let's check if hands are below shoulders (wrists y > shoulder y)
                hands_below_shoulders = 1.0 if (l_wrist[1] > l_shoulder[1] and r_wrist[1] > r_shoulder[1]) else 0.0
                elbow_flex_score = max(0.0, min(1.0, (180.0 - avg_elbow_angle) / 90.0))
                hip_straight_score = max(0.0, min(1.0, (avg_hip_angle - 100.0) / 70.0)) # hips should not be too bent
                scores["Push-up"] = float(hands_below_shoulders * hip_straight_score * (0.3 + 0.7 * elbow_flex_score))
            else:
                scores["Push-up"] = 0.0

            # 3. BENCH PRESS
            # Horizontal spine, back down (wrists closer to sky than shoulders, wrists y < shoulder y)
            if is_horizontal:
                hands_above_shoulders = 1.0 if (l_wrist[1] < l_shoulder[1] and r_wrist[1] < r_shoulder[1]) else 0.0
                elbow_flex_score = max(0.0, min(1.0, (180.0 - avg_elbow_angle) / 90.0))
                scores["Bench Press"] = float(hands_above_shoulders * (0.3 + 0.7 * elbow_flex_score))
            else:
                scores["Bench Press"] = 0.0

            # 4. PULL-UP
            # Vertical spine, hands overhead, elbows pull down
            if is_vertical:
                # Wrists higher than shoulders (wrist y < shoulder y)
                hands_overhead = 1.0 if (l_wrist[1] < l_shoulder[1] or r_wrist[1] < r_shoulder[1]) else 0.0
                # Pull-ups feature high shoulder abduction/adduction
                shoulder_pull_score = max(0.0, min(1.0, avg_shoulder_angle / 150.0))
                scores["Pull-up"] = float(hands_overhead * shoulder_pull_score * 0.9)
            else:
                scores["Pull-up"] = 0.0

            # 5. SHOULDER PRESS
            # Vertical/upright spine, arms pushing overhead
            if is_vertical:
                # Wrists go from shoulder level up to above head
                wrists_high = max(0.0, min(1.0, (l_shoulder[1] - l_wrist[1]) / 0.3)) # positive if wrist above shoulder
                shoulder_open_score = max(0.0, min(1.0, (avg_shoulder_angle - 30.0) / 100.0))
                scores["Shoulder Press"] = float(wrists_high * shoulder_open_score * 0.8)
            else:
                scores["Shoulder Press"] = 0.0

            # 6. BICEP CURL
            # Vertical spine, upper arms stationary, elbow flexion/extension
            if is_vertical:
                # Shoulder angle remains small (arms at side)
                shoulder_tuck_score = max(0.0, min(1.0, (90.0 - avg_shoulder_angle) / 60.0))
                # Elbow flexes/extends
                elbow_movement_score = max(0.0, min(1.0, (180.0 - avg_elbow_angle) / 120.0))
                # Hips/knees are straight
                hips_straight = max(0.0, min(1.0, (avg_hip_angle - 140.0) / 40.0))
                knees_straight = max(0.0, min(1.0, (avg_knee_angle - 140.0) / 40.0))
                
                scores["Bicep Curl"] = float(shoulder_tuck_score * elbow_movement_score * hips_straight * knees_straight)
            else:
                scores["Bicep Curl"] = 0.0

            # 7. DEADLIFT
            # Vertical but hinging spine (spine angle tilts forward, e.g. 25° - 60°)
            # Knees stay mostly straight (angle > 120°), hips hinge deeply (< 130°)
            if is_vertical:
                hinge_score = max(0.0, min(1.0, (spine_angle - 15.0) / 35.0)) # spine tilts forward
                hip_flex_score = max(0.0, min(1.0, (170.0 - avg_hip_angle) / 80.0))
                knee_straight_score = max(0.0, min(1.0, (avg_knee_angle - 110.0) / 60.0)) # knees don't bend as much as squat
                wrists_down = 1.0 if (l_wrist[1] > l_hip[1] and r_wrist[1] > r_hip[1]) else 0.0 # arms hang straight down
                
                scores["Deadlift"] = float(hinge_score * hip_flex_score * knee_straight_score * wrists_down)
            else:
                scores["Deadlift"] = 0.0

            # 8. LUNGES
            # Vertical spine, asymmetric knee flexion
            if is_vertical:
                asymmetry = abs(l_knee_angle - r_knee_angle)
                asymmetry_score = max(0.0, min(1.0, (asymmetry - 15.0) / 70.0)) # asymmetric bending
                one_knee_bent = 1.0 if (l_knee_angle < 130.0 or r_knee_angle < 130.0) else 0.0
                hip_score = max(0.0, min(1.0, (170.0 - avg_hip_angle) / 60.0))
                
                scores["Lunges"] = float(asymmetry_score * one_knee_bent * hip_score)
            else:
                scores["Lunges"] = 0.0

            # Find the best match
            best_exercise = "unknown"
            best_score = 0.0
            
            for exercise, score in scores.items():
                if score > best_score:
                    best_score = score
                    best_exercise = exercise

            # Apply threshold
            if best_score < 0.25:
                return "unknown", 0.0
            
            return best_exercise, float(best_score)

        except Exception:
            return "unknown", 0.0
