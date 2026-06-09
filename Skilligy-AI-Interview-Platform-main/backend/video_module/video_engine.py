# ============================================================
# Video Engine — Frame Extraction for Interview Analysis
# ============================================================

import cv2
import os

def extract_frames(video_path, fps=1):
    """
    Extract frames from video for analysis.
    """

    if not os.path.exists(video_path):
        return []

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        return []

    video_fps = cap.get(cv2.CAP_PROP_FPS)

    if video_fps == 0:
        video_fps = 30

    frame_interval = int(video_fps / fps)

    frames = []
    frame_count = 0

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        if frame_count % frame_interval == 0:

            timestamp = frame_count / video_fps

            frames.append({
                "frame": frame,
                "time": round(timestamp, 2)
            })

        frame_count += 1

    cap.release()

    return frames