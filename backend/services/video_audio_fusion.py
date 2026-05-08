import cv2
import os
import tempfile
import numpy as np
import subprocess
import tensorflow as tf
import librosa
import gc
from tensorflow.keras import backend as K
from backend.utils.save_mood import save_mood

# -----------------------------
# PATHS
# -----------------------------
MODEL_PATH = "backend/models/emotion_model.h5" # Path fix (model vs models)
LABEL_PATH = "backend/models/labels.npy"

# Global pointers
_fusion_model = None
_fusion_labels = None

# Render/Linux compatibility (Windows path removed)
FFMPEG_PATH = "ffmpeg"

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
# AUDIO FEATURES (Optimized)
# -----------------------------
def extract_audio_features(audio_path, sr=22050):
    try:
        audio, _ = librosa.load(audio_path, sr=sr)
        audio, _ = librosa.effects.trim(audio)

        if len(audio) < 1000:
            del audio
            return np.zeros(AUDIO_FEATURE_DIM)

        mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=AUDIO_FEATURE_DIM)
        feat = np.mean(mfcc.T, axis=0)
        
        # 🔥 Clear audio from RAM
        del audio
        return feat
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
            FFMPEG_PATH, "-y",
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
    if total <= 0: return [np.zeros((48, 48, 3), dtype=np.uint8)]
    
    step = max(1, total // FRAMES_TO_SAMPLE)
    i = 0
    while len(frames) < FRAMES_TO_SAMPLE:
        ret, frame = cap.read()
        if not ret: break
        if i % step == 0:
            frames.append(frame)
        i += 1
    cap.release()
    return frames if frames else [np.zeros((48, 48, 3), dtype=np.uint8)]

# -----------------------------
# 🎯 INFERENCE FUNCTION (Deep Cleaned)
# -----------------------------
def predict_video(video_path):
    global _fusion_model, _fusion_labels
    
    try:
        # 1. Lazy Load Model & Labels
        if _fusion_model is None:
            if os.path.exists(MODEL_PATH) and os.path.exists(LABEL_PATH):
                _fusion_model = tf.keras.models.load_model(MODEL_PATH)
                _fusion_labels = np.load(LABEL_PATH)
            else:
                print("❌ Model/Labels not found at paths")
                return "Neutral", 0.0

        # 2. Process Audio
        audio_feat = np.zeros(AUDIO_FEATURE_DIM)
        audio_path = extract_audio(video_path)
        if audio_path:
            audio_feat = extract_audio_features(audio_path)
            if os.path.exists(audio_path): os.unlink(audio_path)

        # 3. Process Video Frames
        frames = extract_frames(video_path)
        frame_feats = np.array([extract_face_features(f) for f in frames])
        face_feat = np.mean(frame_feats, axis=0)

        # 4. Fusion & Prediction
        feat = np.concatenate([face_feat, audio_feat])
        combined = feat[np.newaxis, :]
        pred = _fusion_model.predict(combined, verbose=0)[0]

        idx = int(np.argmax(pred))
        confidence = float(pred[idx]) * 100
        label = str(_fusion_labels[idx]).capitalize() if idx < len(_fusion_labels) else "Neutral"

        # Save Mood
        save_mood(label)

        # 🔥 5. TOTAL RAM PURGE
        # Pointers clean karo aur sessions kill karo
        del _fusion_model
        del _fusion_labels
        _fusion_model = None
        _fusion_labels = None
        
        del frame_feats
        del frames
        
        K.clear_session()
        gc.collect()

        return label, round(confidence, 2)

    except Exception as e:
        print(f"❌ Fusion Error: {e}")
        K.clear_session()
        gc.collect()
        save_mood("Neutral")
        return "Neutral", 0.0
