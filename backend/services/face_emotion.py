import cv2
import numpy as np
import random
import os
import gc
from tensorflow.keras.models import load_model
from tensorflow.keras import backend as K
from backend.utils.save_mood import save_mood

# =========================
# PATH CONFIG
# =========================
MODEL_PATH = "backend/models/emotion_model.hdf5"

# Haar Cascade ko load kar ke rakhte hain (Ye chota hota hai, RAM nahi khata)
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

EMOTIONS = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']

# =========================
# NORMALIZE LABEL
# =========================
def normalize(label):
    mapping = {
        "fear": "Fearful", "surprise": "Surprise",
        "happy": "Happy", "sad": "Sad",
        "angry": "Angry", "neutral": "Neutral",
        "disgust": "Disgust"
    }
    return mapping.get(label.lower(), label)

# =========================
# CONFIDENCE ENGINE (Optimized)
# =========================
def compute_confidence(preds, emotion):
    base_conf = float(np.max(preds)) * 100
    emotion_weights = {
        "happy": 1.05, "neutral": 0.90, "sad": 0.95,
        "angry": 0.98, "fear": 0.85, "surprise": 1.10, "disgust": 0.80
    }
    confidence = base_conf * emotion_weights.get(emotion.lower(), 1.0)
    confidence *= random.uniform(0.85, 1.15) # Randomness range narrow kiya for stability
    confidence = (confidence * 0.88) + 6
    return round(max(20.0, min(confidence, 100.0)), 2)

# =========================
# MAIN FUNCTION (Speed Optimized)
# =========================
def detect_face_emotion(frame):
    model = None
    try:
        # 1. Image Resize (Detection fast karne ke liye)
        small_frame = cv2.resize(frame, (320, 240))
        gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)

        # 2. Fast Face Detection (minNeighbors badhaya taaki false positive kam hon)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) == 0:
            return "no_face", 0.0

        # 3. Model Loading (Sirf prediction ke waqt)
        if model is None:
            model = load_model(MODEL_PATH)

        # Largest face selection
        (x, y, w, h) = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)[0]
        face = gray[y:y+h, x:x+w]
        face = cv2.resize(face, (48, 48))
        face = face.astype("float32") / 255.0
        face = np.expand_dims(face, axis=(0, -1))

        # 4. Prediction
        preds = model.predict(face, verbose=0)[0]
        idx = np.argmax(preds)
        emotion = normalize(EMOTIONS[idx])
        confidence = compute_confidence(preds, emotion)

        # Save Mood
        if confidence > 50:
            save_mood(emotion)

        # 🔥 5. RAM CLEARING (Sabse zaroori)
        # Model ka kaam khatam, ab ise RAM se nikaalo
        del model
        K.clear_session()
        gc.collect()

        return emotion, confidence

    except Exception as e:
        print(f"❌ Face Emotion Error: {e}")
        # Error aane par bhi RAM saaf karne ki koshish karein
        K.clear_session()
        gc.collect()
        return "error", 0.0
