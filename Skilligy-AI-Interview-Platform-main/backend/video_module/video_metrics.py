# ============================================================
# Video Metrics — Explainable Behavioral Signals
# ============================================================

import numpy as np


# ------------------------------------------------------------
# Face visibility
# ------------------------------------------------------------
def face_visibility_ratio(frame_results):

    if not frame_results:
        return 0

    visible = sum(1 for r in frame_results if r["face_detected"])

    return round((visible / len(frame_results)) * 100, 1)


# ------------------------------------------------------------
# Eye orientation (approximate camera-facing)
# ------------------------------------------------------------
def eye_contact_ratio(frame_results):
    """
    Approximate eye contact using relative eye center position.
    This is NOT gaze prediction — only orientation consistency.
    """

    valid = 0
    forward = 0

    for r in frame_results:

        if not r["face_detected"]:
            continue

        landmarks = r["landmarks"]

        # Safety check
        if len(landmarks) < 264:
            continue

        # MediaPipe eye landmarks
        left_eye = landmarks[33]
        right_eye = landmarks[263]
        nose = landmarks[1]

        eye_center_x = (left_eye[0] + right_eye[0]) / 2
        nose_x = nose[0]

        # Increased tolerance for webcam noise
        if abs(eye_center_x - nose_x) < 30:
            forward += 1

        valid += 1

    if valid == 0:
        return 0

    return round((forward / valid) * 100, 1)


# ------------------------------------------------------------
# Head movement stability
# ------------------------------------------------------------
def head_movement_level(frame_results):
    """
    Measure landmark displacement between frames.
    """

    movements = []

    prev = None

    for r in frame_results:

        if not r["face_detected"]:
            continue

        curr = np.array(r["landmarks"])

        if prev is not None:

            diff = np.mean(
                np.linalg.norm(curr - prev, axis=1)
            )

            movements.append(diff)

        prev = curr

    if not movements:
        return "low"

    avg = np.mean(movements)

    # Adjusted thresholds (less sensitive)
    if avg < 4:
        return "stable"

    elif avg < 8:
        return "moderate"

    else:
        return "high"


# ------------------------------------------------------------
# Facial activity (expressiveness)
# ------------------------------------------------------------
def facial_activity_level(frame_results):
    """
    Measure mouth movement across frames.
    """

    activity = []

    prev = None

    for r in frame_results:

        if not r["face_detected"]:
            continue

        curr = np.array(r["landmarks"])

        if prev is not None:

            # Mouth landmarks (approx)
            mouth = curr[61:68]
            prev_mouth = prev[61:68]

            diff = np.mean(
                np.linalg.norm(mouth - prev_mouth, axis=1)
            )

            activity.append(diff)

        prev = curr

    if not activity:
        return "low"

    avg = np.mean(activity)

    # Adjusted thresholds
    if avg < 2:
        return "low"

    elif avg < 6:
        return "moderate"

    else:
        return "high"


# ------------------------------------------------------------
# Engagement score (rule-based)
# ------------------------------------------------------------
def engagement_score(face_ratio, eye_ratio, head_level):

    score = 0

    # Face visibility
    if face_ratio > 80:
        score += 4

    elif face_ratio > 60:
        score += 3

    else:
        score += 1

    # Eye contact
    if eye_ratio > 70:
        score += 4

    elif eye_ratio > 50:
        score += 3

    else:
        score += 1

    # Head movement
    if head_level == "stable":
        score += 2

    elif head_level == "moderate":
        score += 1

    return min(10, score)