# ============================================================
# Face Analysis - Landmark Detection (New MediaPipe API)
# ============================================================
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import urllib.request
import os

# Download face landmarker model if not present
MODEL_PATH = "face_landmarker.task"
if not os.path.exists(MODEL_PATH):
    print("Downloading face landmarker model...")
    urllib.request.urlretrieve(
        "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
        MODEL_PATH
    )
    print("Model downloaded!")

base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    num_faces=1,
    min_face_detection_confidence=0.5
)
detector = vision.FaceLandmarker.create_from_options(options)

def analyze_frame(frame):
    if frame is None:
        return {"face_detected": False, "landmarks": []}

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = detector.detect(mp_image)

    if not result.face_landmarks:
        return {"face_detected": False, "landmarks": []}

    h, w, _ = frame.shape
    landmarks = []
    for lm in result.face_landmarks[0]:
        x = int(lm.x * w)
        y = int(lm.y * h)
        landmarks.append((x, y))

    return {"face_detected": True, "landmarks": landmarks}
