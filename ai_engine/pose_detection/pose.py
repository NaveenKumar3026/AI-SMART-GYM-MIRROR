import numpy as np
from typing import Dict, Tuple, Any

# Map MediaPipe landmarks to names
LANDMARKS = {
    "NOSE": 0,
    "LEFT_EYE_INNER": 1, "LEFT_EYE": 2, "LEFT_EYE_OUTER": 3,
    "RIGHT_EYE_INNER": 4, "RIGHT_EYE": 5, "RIGHT_EYE_OUTER": 6,
    "LEFT_EAR": 7, "RIGHT_EAR": 8,
    "MOUTH_LEFT": 9, "MOUTH_RIGHT": 10,
    "LEFT_SHOULDER": 11, "RIGHT_SHOULDER": 12,
    "LEFT_ELBOW": 13, "RIGHT_ELBOW": 14,
    "LEFT_WRIST": 15, "RIGHT_WRIST": 16,
    "LEFT_PINKY": 17, "RIGHT_PINKY": 18,
    "LEFT_INDEX": 19, "RIGHT_INDEX": 20,
    "LEFT_THUMB": 21, "RIGHT_THUMB": 22,
    "LEFT_HIP": 23, "RIGHT_HIP": 24,
    "LEFT_KNEE": 25, "RIGHT_KNEE": 26,
    "LEFT_ANKLE": 27, "RIGHT_ANKLE": 28,
    "LEFT_HEEL": 29, "RIGHT_HEEL": 30,
    "LEFT_FOOT_INDEX": 31, "RIGHT_FOOT_INDEX": 32
}

def calculate_angle(p1: Tuple[float, float, float], 
                    p2: Tuple[float, float, float], 
                    p3: Tuple[float, float, float]) -> float:
    """
    Calculates the angle between three 3D points where p2 is the vertex.
    Returns angle in degrees.
    """
    ba = np.array(p1) - np.array(p2)
    bc = np.array(p3) - np.array(p2)

    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)
    
    if norm_ba < 1e-6 or norm_bc < 1e-6:
        return 180.0

    cosine_angle = np.dot(ba, bc) / (norm_ba * norm_bc)
    cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
    angle = np.arccos(cosine_angle)
    
    return float(np.degrees(angle))

def get_landmark_coords(landmarks: list, name: str) -> Tuple[float, float, float]:
    """
    Extract x, y, z coordinates for a specific landmark index/name.
    Accepts landmarks as a list of dicts, objects, or a flat list.
    """
    idx = LANDMARKS.get(name)
    if idx is None:
        raise ValueError(f"Unknown landmark: {name}")
        
    if idx >= len(landmarks):
        return (0.0, 0.0, 0.0)
        
    lm = landmarks[idx]
    if isinstance(lm, dict):
        return (lm.get("x", 0.0), lm.get("y", 0.0), lm.get("z", 0.0))
    elif hasattr(lm, "x"):
        return (lm.x, lm.y, lm.z)
    elif isinstance(lm, (list, tuple)) and len(lm) >= 3:
        return (lm[0], lm[1], lm[2])
    return (0.0, 0.0, 0.0)

def extract_angles(landmarks: list) -> Dict[str, float]:
    """
    Calculates key joint angles for exercise classification and form feedback.
    """
    if not landmarks or len(landmarks) < 33:
        return {}

    try:
        # Left side
        l_shoulder = get_landmark_coords(landmarks, "LEFT_SHOULDER")
        l_elbow = get_landmark_coords(landmarks, "LEFT_ELBOW")
        l_wrist = get_landmark_coords(landmarks, "LEFT_WRIST")
        l_hip = get_landmark_coords(landmarks, "LEFT_HIP")
        l_knee = get_landmark_coords(landmarks, "LEFT_KNEE")
        l_ankle = get_landmark_coords(landmarks, "LEFT_ANKLE")

        # Right side
        r_shoulder = get_landmark_coords(landmarks, "RIGHT_SHOULDER")
        r_elbow = get_landmark_coords(landmarks, "RIGHT_ELBOW")
        r_wrist = get_landmark_coords(landmarks, "RIGHT_WRIST")
        r_hip = get_landmark_coords(landmarks, "RIGHT_HIP")
        r_knee = get_landmark_coords(landmarks, "RIGHT_KNEE")
        r_ankle = get_landmark_coords(landmarks, "RIGHT_ANKLE")

        # Angles
        angles = {
            "left_elbow": calculate_angle(l_shoulder, l_elbow, l_wrist),
            "right_elbow": calculate_angle(r_shoulder, r_elbow, r_wrist),
            "left_knee": calculate_angle(l_hip, l_knee, l_ankle),
            "right_knee": calculate_angle(r_hip, r_knee, r_ankle),
            "left_hip": calculate_angle(l_shoulder, l_hip, l_knee),
            "right_hip": calculate_angle(r_shoulder, r_hip, r_knee),
            "left_shoulder": calculate_angle(l_hip, l_shoulder, l_elbow),
            "right_shoulder": calculate_angle(r_hip, r_shoulder, r_elbow),
        }
        
        # Spine alignment: angle between spine (mid-hip to mid-shoulder) and horizontal/vertical
        mid_hip = ((l_hip[0] + r_hip[0]) / 2.0, (l_hip[1] + r_hip[1]) / 2.0, (l_hip[2] + r_hip[2]) / 2.0)
        mid_shoulder = ((l_shoulder[0] + r_shoulder[0]) / 2.0, (l_shoulder[1] + r_shoulder[1]) / 2.0, (l_shoulder[2] + r_shoulder[2]) / 2.0)
        
        # Spine vertical deviation (angle relative to absolute vertical [0, -1, 0] in MediaPipe where Y goes down)
        spine_vector = np.array(mid_shoulder) - np.array(mid_hip)
        vertical_vector = np.array([0.0, -1.0, 0.0])
        
        norm_spine = np.linalg.norm(spine_vector)
        if norm_spine > 1e-6:
            cosine_spine = np.dot(spine_vector, vertical_vector) / (norm_spine * np.linalg.norm(vertical_vector))
            spine_angle = np.arccos(np.clip(cosine_spine, -1.0, 1.0))
            angles["spine_angle"] = float(np.degrees(spine_angle))
        else:
            angles["spine_angle"] = 0.0
        
        return angles
    except Exception:
        return {}
