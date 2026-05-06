import os
import pickle

# ✅ ADD THIS IMPORT
from backend.utils.save_mood import save_mood

MODEL_PATH = "backend/models/text_model.pkl"
VECTORIZER_PATH = "backend/models/vectorizer.pkl"

model = None
vectorizer = None

if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
    try:
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)

        with open(VECTORIZER_PATH, "rb") as f:
            vectorizer = pickle.load(f)

        print("✅ Text model loaded")

    except Exception as e:
        print("❌ Load error:", e)


def normalize_label(label):
    mapping = {
        "fear": "Fearful",
        "surprised": "Surprise",
        "surprise": "Surprise",
        "happy": "Happy",
        "sad": "Sad",
        "angry": "Angry",
        "neutral": "Neutral"
    }
    return mapping.get(str(label).lower(), str(label).capitalize())


def clean_text(text):
    return str(text).lower().strip()


def rule_engine(text):

    if "!" in text or any(w in text for w in ["wow", "omg", "amazing"]):
        return "Surprise", 95

    if any(w in text for w in ["happy", "great", "awesome", "good", "khush"]):
        return "Happy", 90

    if any(w in text for w in ["sad", "depressed", "cry", "dukhi", "udaas"]):
        return "Sad", 90

    if any(w in text for w in ["angry", "mad", "hate", "gussa"]):
        return "Angry", 90

    if any(w in text for w in ["fear", "scared", "dar"]):
        return "Fearful", 88

    return None, 0


def detect_text_emotion(text):

    if not text:
        emotion = "Neutral"
        save_mood(emotion)   # ✅ ADD
        return emotion, 0.0

    try:
        text = clean_text(text)

        # RULE FIRST
        label, conf = rule_engine(text)
        if label:
            conf = max(0.0, min(float(conf), 100.0))
            save_mood(label)   # ✅ ADD
            return label, round(conf, 2)

        # ML MODEL
        if model and vectorizer:
            vec = vectorizer.transform([text])

            pred = model.predict(vec)[0]

            # ✅ FIX START (REALISTIC CONFIDENCE)
            if hasattr(model, "predict_proba"):
                prob = model.predict_proba(vec)[0]

                max_prob = float(max(prob))

                # 🔥 IMPORTANT FIX:
                confidence = max_prob * 100.0

                confidence = (confidence * 0.85) + 10

            else:
                confidence = 60.0

            confidence = max(0.0, min(confidence, 100.0))

            emotion = normalize_label(pred)

            save_mood(emotion)   # ✅ ADD (MOST IMPORTANT)

            return emotion, round(confidence, 2)

        emotion = "Neutral"
        save_mood(emotion)   # ✅ ADD
        return emotion, 50.0

    except Exception as e:
        print("❌ Text error:", e)
        emotion = "Neutral"
        save_mood(emotion)   # ✅ ADD
        return emotion, 0.0