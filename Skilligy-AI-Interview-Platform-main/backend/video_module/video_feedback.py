# ============================================================
# Video Feedback — Human, Interviewer-Style Coaching
# ============================================================

def generate_video_feedback(metrics):

    feedback = []
    score = 0

    # Face visibility
    face_ratio = metrics.get("face_visibility", 0)

    if face_ratio >= 80:
        feedback.append(
            "Your face stayed clearly visible throughout most of the answer, which creates a confident and professional impression."
        )
        score += 3

    elif face_ratio >= 60:
        feedback.append(
            "Your face was visible for most of the response, but adjusting your camera slightly could improve your on-screen presence."
        )
        score += 2

    else:
        feedback.append(
            "Your face moved out of frame multiple times. Try positioning the camera at eye level and staying centered."
        )
        score += 1


    # Eye contact
    eye_ratio = metrics.get("eye_contact", 0)

    if eye_ratio >= 70:
        feedback.append(
            "You maintained strong eye contact with the camera, which helps build trust and engagement."
        )
        score += 3

    elif eye_ratio >= 50:
        feedback.append(
            "Your eye contact was fairly consistent, though a few moments of looking away were noticed."
        )
        score += 2

    else:
        feedback.append(
            "You often looked away from the camera. Maintaining eye contact will make your answers feel more confident."
        )
        score += 1


    # Head movement
    head = metrics.get("head_movement", "moderate")

    if head == "stable":
        feedback.append(
            "Your head movement was steady and composed, which reflects confidence."
        )
        score += 2

    elif head == "moderate":
        feedback.append(
            "Some natural head movement was observed, which is fine as long as it remains controlled."
        )
        score += 1

    else:
        feedback.append(
            "There was noticeable head movement that could distract the interviewer. Try to stay a bit more still."
        )


    # Facial activity
    facial = metrics.get("facial_activity", "moderate")

    if facial == "moderate":
        feedback.append(
            "Your facial expressions were balanced and appropriate for an interview setting."
        )
        score += 2

    elif facial == "low":
        feedback.append(
            "Your facial expressions were minimal. Slightly more expressiveness can help emphasize key points."
        )
        score += 1

    else:
        feedback.append(
            "You showed high facial expressiveness. Make sure it remains natural and professional."
        )
        score += 1


    # Normalize to score out of 10
    video_score = min(10, score)

    return {
        "video_score": video_score,
        "feedback": feedback
    }