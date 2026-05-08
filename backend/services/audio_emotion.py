import numpy as np
import pickle
import librosa
import os
import gc
import sys
from tensorflow.keras.models import load_model
from tensorflow.keras import backend as K
from backend.utils.save_mood import save_mood

# -------------------------
# PATHS
# -------------------------
MODEL_PATH = "backend/models/audio_model.h5"
ENCODER_PATH = "backend/models/audio_label_encoder.pkl"

# Global pointers (shuruat mein khali)
_model = None
_encoder = None

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
        # sr=22050 standard hai, mono=True RAM bachata hai
        audio, sr = librosa.load(file_path, sr=22050, mono=True)

        if np.max(np.abs(audio)) < 0.01:
            del audio # Turant delete karo
            return None

        # 3 second ki limit (RAM management)
        max_len = 3 * sr
        audio = audio[:max_len] if len(audio) > max_len else np.pad(
            audio, (0, max_len - len(audio))
        )

        mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=40)
        feature_vector = np.mean(mfcc.T, axis=0)
        
        # 🔥 Cleanup audio array from memory
        del audio
        return feature_vector

    except Exception as e:
        print(f"❌ Feature Extraction Error: {e}")
        return None

def detect_audio_emotion(file_path):
    global _model, _encoder
    
    try:
        # 1. Lazy Load: Jab zaroorat ho tabhi load karo
        if _model is None and os.path.exists(MODEL_PATH):
            _model = load_model(MODEL_PATH)
        
        if _encoder is None and os.path.exists(ENCODER_PATH):
            with open(ENCODER_PATH, "rb") as f:
                _encoder = pickle.load(f)

        if _model is None or _encoder is None:
            return "Neutral", 0.0

        # 2. Extract Features
        features = extract_features(file_path)

        if features is None:
            emotion = "Neutral"
            save_mood(emotion)
            return emotion, 0.0

        # 3. Predict
        features_input = np.expand_dims(features, axis=0)
        pred = _model.predict(features_input, verbose=0)[0]
        idx = np.argmax(pred)

        # 4. Confidence Logic (Tere original formulas ke saath)
        confidence = float(pred[idx]) * 100.0
        confidence = (confidence * 0.9) + 5
        confidence = max(0.0, min(confidence, 100.0))

        if confidence < 40:
            label = "Neutral"
        else:
            label = _encoder.inverse_transform([idx])[0]
            label = normalize_label(label)

        # Final Save
        save_mood(label)

        # 🔥 5. DEEP CLEANUP (Sabse zaroori Render ke liye)
        # Prediction ke baad pointers ko reset karo aur RAM release karo
        del _model
        del _encoder
        _model = None
        _encoder = None
        
        K.clear_session()
        gc.collect()

        return label, round(confidence, 2)

    except Exception as e:
        print("❌ Audio emotion error:", e)
        # Error aane par bhi memory saaf karo
        K.clear_session()
        gc.collect()
        emotion = "Neutral"
        save_mood(emotion)
        return emotion, 0.0
