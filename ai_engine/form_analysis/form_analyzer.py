from typing import Dict, List, Any, Tuple
from ai_engine.pose_detection.pose import extract_angles, get_landmark_coords

class FormAnalyzer:
    def analyze(self, exercise: str, landmarks: list, state: str) -> Dict[str, Any]:
        """
        Analyzes form biomechanics for a given exercise and frame state.
        Returns:
            {
                "form_score": int (0-100),
                "issues": list of dicts,
                "feedback": str (verbal coaching cue)
            }
        """
        if not landmarks or len(landmarks) < 33:
            return {"form_score": 100, "issues": [], "feedback": "Ready."}

        angles = extract_angles(landmarks)
        if not angles:
            return {"form_score": 100, "issues": [], "feedback": "Ready."}

        issues = []
        feedbacks = []
        scores = []

        try:
            # Load joint coordinates
            l_shoulder = get_landmark_coords(landmarks, "LEFT_SHOULDER")
            r_shoulder = get_landmark_coords(landmarks, "RIGHT_SHOULDER")
            l_hip = get_landmark_coords(landmarks, "LEFT_HIP")
            r_hip = get_landmark_coords(landmarks, "RIGHT_HIP")
            l_knee = get_landmark_coords(landmarks, "LEFT_KNEE")
            r_knee = get_landmark_coords(landmarks, "RIGHT_KNEE")
            l_ankle = get_landmark_coords(landmarks, "LEFT_ANKLE")
            r_ankle = get_landmark_coords(landmarks, "RIGHT_ANKLE")
            l_elbow = get_landmark_coords(landmarks, "LEFT_ELBOW")
            r_elbow = get_landmark_coords(landmarks, "RIGHT_ELBOW")

            l_knee_angle = angles.get("left_knee", 180.0)
            r_knee_angle = angles.get("right_knee", 180.0)
            avg_knee = (l_knee_angle + r_knee_angle) / 2.0

            l_hip_angle = angles.get("left_hip", 180.0)
            r_hip_angle = angles.get("right_hip", 180.0)
            avg_hip = (l_hip_angle + r_hip_angle) / 2.0

            l_elbow_angle = angles.get("left_elbow", 180.0)
            r_elbow_angle = angles.get("right_elbow", 180.0)
            avg_elbow = (l_elbow_angle + r_elbow_angle) / 2.0

            l_shoulder_angle = angles.get("left_shoulder", 0.0)
            r_shoulder_angle = angles.get("right_shoulder", 0.0)
            avg_shoulder = (l_shoulder_angle + r_shoulder_angle) / 2.0

            spine_angle = angles.get("spine_angle", 0.0)

            # Analyze based on exercise
            if exercise == "Squat":
                # 1. Squat Depth (only check at bottom/mid states)
                if state in ["DOWN", "GOING_UP", "GOING_DOWN"]:
                    # Hips should go parallel to knees (hip y >= knee y in MediaPipe where y down is positive)
                    # Also knee angles should flex below 105 degrees
                    hip_y_avg = (l_hip[1] + r_hip[1]) / 2.0
                    knee_y_avg = (l_knee[1] + r_knee[1]) / 2.0
                    
                    if hip_y_avg < knee_y_avg - 0.02 and avg_knee > 110.0:
                        score_depth = 60
                        scores.append(score_depth)
                        issues.append({
                            "code": "POOR_DEPTH",
                            "joint": "Hip & Knee",
                            "severity": "medium",
                            "score": score_depth,
                            "suggestion": "Squat lower! Try to get your thighs parallel to the floor."
                        })
                        feedbacks.append("Go deeper")
                    else:
                        scores.append(100)

                # 2. Knee Valgus (Knees caving in)
                # Compare knee width to ankle and hip width
                hip_width = abs(l_hip[0] - r_hip[0])
                knee_width = abs(l_knee[0] - r_knee[0])
                ankle_width = abs(l_ankle[0] - r_ankle[0])
                
                # Knees caving in if knee width is significantly smaller than ankle or hip width
                if knee_width < hip_width * 0.85 or knee_width < ankle_width * 0.85:
                    score_valgus = 70
                    scores.append(score_valgus)
                    issues.append({
                        "code": "KNEE_VALGUS",
                        "joint": "Knee",
                        "severity": "high",
                        "score": score_valgus,
                        "suggestion": "Drive your knees outward; don't let them cave inward."
                    })
                    feedbacks.append("Knees out")
                else:
                    scores.append(100)

                # 3. Back Rounding (spine vertical angle tilts too far forward or arches)
                if state in ["GOING_DOWN", "DOWN", "GOING_UP"]:
                    if spine_angle > 40.0: # excessive forward tilt
                        score_back = 75
                        scores.append(score_back)
                        issues.append({
                            "code": "ROUNDED_BACK",
                            "joint": "Spine",
                            "severity": "medium",
                            "score": score_back,
                            "suggestion": "Keep your chest up and core engaged to protect your back."
                        })
                        feedbacks.append("Chest up")
                    else:
                        scores.append(100)

            elif exercise in ["Push-up", "Bench Press"]:
                # 1. Elbow Flare (arms flared out to sides > 70 deg)
                # Tuck elbows: shoulder angle (hip-shoulder-elbow) should be < 65 deg
                if avg_shoulder > 70.0:
                    score_flare = 65
                    scores.append(score_flare)
                    issues.append({
                        "code": "ELBOW_FLARE",
                        "joint": "Shoulder",
                        "severity": "medium",
                        "score": score_flare,
                        "suggestion": "Tuck your elbows closer to your body (~45 degrees) to protect your shoulders."
                    })
                    feedbacks.append("Tuck elbows")
                else:
                    scores.append(100)

                # 2. Hips Sagging (Push-up only)
                if exercise == "Push-up":
                    # Hip angle should be straight (140-180 deg)
                    if avg_hip < 135.0:
                        score_hips = 70
                        scores.append(score_hips)
                        issues.append({
                            "code": "HIPS_SAGGING",
                            "joint": "Hip",
                            "severity": "high",
                            "score": score_hips,
                            "suggestion": "Keep your core tight and body in a straight line. Don't let your hips sag."
                        })
                        feedbacks.append("Tighten core")
                    else:
                        scores.append(100)

            elif exercise == "Deadlift":
                # 1. Spine alignment (Rounded back is highly dangerous)
                # In Deadlift, the spine angle relative to vertical tilts forward, but it MUST be a straight line.
                # If spine angle tilts forward (> 30 deg) and the shoulders/hips lose rigidity (hip angle < 100),
                # we check if the spine is curved. A straight spine maintains a consistent relation.
                # If hip hinges deeply (avg_hip < 120) but spine angle is very high (> 55),
                # check if shoulders are dropping.
                if state in ["GOING_UP", "GOING_DOWN", "DOWN"]:
                    if spine_angle > 65.0:
                        score_spine = 50
                        scores.append(score_spine)
                        issues.append({
                            "code": "ROUNDED_BACK",
                            "joint": "Spine",
                            "severity": "critical",
                            "score": score_spine,
                            "suggestion": "CRITICAL: Neutral spine! Flatten your back and pull your shoulders back."
                        })
                        feedbacks.append("Flatten back!")
                    else:
                        scores.append(100)

                # 2. Knee Bend (Deadlifts are not squats)
                # If knee bend is too deep (avg_knee < 105), they are squatting the deadlift
                if avg_knee < 110.0 and state in ["DOWN", "GOING_UP"]:
                    score_deadlift_knee = 80
                    scores.append(score_deadlift_knee)
                    issues.append({
                        "code": "KNEE_OVERBENT",
                        "joint": "Knee",
                        "severity": "low",
                        "score": score_deadlift_knee,
                        "suggestion": "Keep your hips higher. Hinge at your hips rather than squatting the weight."
                    })
                    feedbacks.append("Hips higher")
                else:
                    scores.append(100)

            elif exercise == "Bicep Curl":
                # 1. Upper arms swaying (shoulder angle should remain small < 25)
                if avg_shoulder > 30.0:
                    score_sway = 75
                    scores.append(score_sway)
                    issues.append({
                        "code": "ARM_SWAY",
                        "joint": "Shoulder",
                        "severity": "medium",
                        "score": score_sway,
                        "suggestion": "Keep your elbows locked at your sides. Avoid swinging your upper arms."
                    })
                    feedbacks.append("Keep elbows still")
                else:
                    scores.append(100)

            elif exercise == "Shoulder Press":
                # 1. Arching back (excessive spine lean or hip forward)
                # Spine angle relative to vertical should stay small (< 20)
                if spine_angle > 22.0:
                    score_arch = 70
                    scores.append(score_arch)
                    issues.append({
                        "code": "ARCHING_BACK",
                        "joint": "Spine",
                        "severity": "high",
                        "score": score_arch,
                        "suggestion": "Keep your core braced and torso upright. Avoid arching your lower back."
                    })
                    feedbacks.append("Brace core")
                else:
                    scores.append(100)

            elif exercise == "Lunges":
                # 1. Forward Knee Travel (front knee angle too sharp, knee going past ankle)
                # Front leg knee angle bends too deeply (< 80)
                min_knee = min(l_knee_angle, r_knee_angle)
                if min_knee < 80.0:
                    score_travel = 75
                    scores.append(score_travel)
                    issues.append({
                        "code": "KNEE_TRAVEL",
                        "joint": "Knee",
                        "severity": "medium",
                        "score": score_travel,
                        "suggestion": "Take a larger step forward to keep your front knee behind your toes."
                    })
                    feedbacks.append("Step wider")
                else:
                    scores.append(100)

            # Final Score calculation (average of all metric checks)
            final_score = int(sum(scores) / len(scores)) if scores else 100
            
            # Default feedback if no issues
            if not feedbacks:
                if state == "UP" and exercise in ["Squat", "Push-up", "Bench Press"]:
                    feedback_str = "Excellent extension. Core tight."
                elif state == "DOWN" and exercise in ["Pull-up", "Shoulder Press", "Bicep Curl"]:
                    feedback_str = "Good stretch at the bottom."
                elif state in ["GOING_UP", "GOING_DOWN"]:
                    feedback_str = "Control the movement."
                else:
                    feedback_str = "Good form! Keep going."
            else:
                feedback_str = feedbacks[0]  # Return the highest priority feedback

            return {
                "form_score": final_score,
                "issues": issues,
                "feedback": feedback_str
            }

        except Exception as e:
            return {"form_score": 100, "issues": [], "feedback": "Ready."}
