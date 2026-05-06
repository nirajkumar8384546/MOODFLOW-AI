# services/video_audio_fusion.py
#video_audio_fusion.py
import cv2
import os
import tempfile
import numpy as np
import subprocess
import tensorflow as tf
import librosa

# ✅ ADD THIS IMPORT
from backend.utils.save_mood import save_mood

# -----------------------------
# PATHS
# -----------------------------
MODEL_PATH = "backend/model/emotion_model.h5"
LABEL_PATH = "backend/model/labels.npy"

# -----------------------------
# SAFE MODEL LOAD (🔥 FIX)
# -----------------------------
model = None
LABELS = ["Neutral"]
FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"
if os.path.exists(MODEL_PATH) and os.path.exists(LABEL_PATH):
    try:
        model = tf.keras.models.load_model(MODEL_PATH)
        LABELS = np.load(LABEL_PATH)
        print("✅ Model loaded")
    except Exception as e:
        print("❌ Model load failed:", e)
else:
    print("✅ Multimodel loaded")

# -----------------------------
# CONSTANTS
# -----------------------------
FRAME_SIZE = (48, 48)
AUDIO_FEATURE_DIM = 40
FRAMES_TO_SAMPLE = 20

# -----------------------------
# FACE FEATURES
# -----------------------------
def extract_face_features(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, FRAME_SIZE)
    gray = gray / 255.0
    return gray.flatten()

# -----------------------------
# AUDIO FEATURES
# -----------------------------
def extract_audio_features(audio_path, sr=22050):
    try:
        audio, _ = librosa.load(audio_path, sr=sr)
        audio, _ = librosa.effects.trim(audio)

        if len(audio) < 1000:
            return np.zeros(AUDIO_FEATURE_DIM)

        mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=AUDIO_FEATURE_DIM)
        return np.mean(mfcc.T, axis=0)

    except Exception as e:
        print("❌ Audio feature error:", e)
        return np.zeros(AUDIO_FEATURE_DIM)

# -----------------------------
# AUDIO EXTRACT
# -----------------------------
def extract_audio(video_path):
    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")

    try:
        subprocess.run([
            "ffmpeg", "-y",
            "-i", video_path,
            "-ac", "1",
            "-ar", "22050",
            temp_audio.name
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if os.path.exists(temp_audio.name):
            return temp_audio.name

    except Exception as e:
        print("❌ FFmpeg error:", e)

    return None

# -----------------------------
# FRAME SAMPLING
# -----------------------------
def extract_frames(video_path):
    cap = cv2.VideoCapture(video_path)
    frames = []

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(1, total // FRAMES_TO_SAMPLE)

    i = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if i % step == 0:
            frames.append(frame)

        i += 1

    cap.release()

    if len(frames) == 0:
        return [np.zeros((48, 48, 3), dtype=np.uint8)]

    return frames

# -----------------------------
# 🔥 TRAINING FUNCTION
# -----------------------------
def process_video(video_path):
    audio_feat = np.zeros(AUDIO_FEATURE_DIM)
    audio_path = extract_audio(video_path)

    if audio_path:
        try:
            audio_feat = extract_audio_features(audio_path)
        finally:
            if os.path.exists(audio_path):
                os.unlink(audio_path)

    frames = extract_frames(video_path)

    frame_feats = np.array([
        extract_face_features(f) for f in frames
    ])

    face_feat = np.mean(frame_feats, axis=0)

    return np.concatenate([face_feat, audio_feat])

# -----------------------------
# 🎯 INFERENCE FUNCTION
# -----------------------------
def predict_video(video_path):

    if model is None:
        emotion = "Neutral"
        save_mood(emotion)   # ✅ ADD
        return emotion, 0.0

    feat = process_video(video_path)
    combined = feat[np.newaxis, :]

    pred = model.predict(combined, verbose=0)[0]

    idx = int(np.argmax(pred))
    confidence = float(pred[idx]) * 100

    confidence = max(0.0, min(confidence, 100.0))

    label = LABELS[idx] if idx < len(LABELS) else "Neutral"

    # ✅ normalize (optional but clean)
    label = str(label).capitalize()

    # ✅ FINAL SAVE (MOST IMPORTANT)
    save_mood(label)

    return label, round(confidence, 2)