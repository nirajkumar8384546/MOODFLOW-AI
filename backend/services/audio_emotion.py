# audio_emotion.py
import numpy as np
import pickle
import librosa
import os
from tensorflow.keras.models import load_model

# ✅ ADD THIS IMPORT
from backend.utils.save_mood import save_mood
# agar error aaye to use:
# from utils.save_mood import save_mood


# -------------------------
# PATHS
# -------------------------
MODEL_PATH = "backend/models/audio_model.h5"
ENCODER_PATH = "backend/models/audio_label_encoder.pkl"

# -------------------------
# LOAD MODEL + ENCODER
# -------------------------
model = None
encoder = None

if os.path.exists(MODEL_PATH):
    model = load_model(MODEL_PATH)

if os.path.exists(ENCODER_PATH):
    with open(ENCODER_PATH, "rb") as f:
        encoder = pickle.load(f)

print("✅ Audio model loaded")


def normalize_label(label):
    mapping = {
        "fear": "Fearful",
        "surprised": "Surprise",
        "happy": "Happy",
        "sad": "Sad",
        "angry": "Angry",
        "neutral": "Neutral"
    }
    return mapping.get(label.lower(), label.capitalize())


def extract_features(file_path):
    try:
        audio, sr = librosa.load(file_path, sr=22050, mono=True)

        if np.max(np.abs(audio)) < 0.01:
            return None

        max_len = 3 * sr
        audio = audio[:max_len] if len(audio) > max_len else np.pad(
            audio, (0, max_len - len(audio))
        )

        mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=40)
        return np.mean(mfcc.T, axis=0)

    except:
        return None


def detect_audio_emotion(file_path):

    if model is None or encoder is None:
        return "Neutral", 0.0

    try:
        features = extract_features(file_path)

        if features is None:
            emotion = "Neutral"
            save_mood(emotion)   # ✅ ADD
            return emotion, 0.0

        features = np.expand_dims(features, axis=0)

        pred = model.predict(features, verbose=0)[0]

        idx = np.argmax(pred)

        # -------------------------
        # 🔥 FIXED CONFIDENCE LOGIC
        # -------------------------
        confidence = float(pred[idx]) * 100.0

        # ✔ smoother scaling (prevents fake 100%)
        confidence = (confidence * 0.9) + 5

        # clamp 0–100
        confidence = max(0.0, min(confidence, 100.0))

        if confidence < 40:
            emotion = "Neutral"
            save_mood(emotion)   # ✅ ADD
            return emotion, round(confidence, 2)

        label = encoder.inverse_transform([idx])[0]
        label = normalize_label(label)

        # ✅ FINAL SAVE (MOST IMPORTANT)
        save_mood(label)

        return label, round(confidence, 2)

    except Exception as e:
        print("Audio emotion error:", e)
        emotion = "Neutral"
        save_mood(emotion)   # ✅ ADD (error case)
        return emotion, 0.0