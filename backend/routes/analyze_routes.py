from flask import Blueprint, request, jsonify
import cv2
import numpy as np
import os
import tempfile
import subprocess
import gc  # 🔥 Garbage Collector for RAM
from tensorflow.keras import backend as K  # 🔥 To clear TF sessions

analyze_bp = Blueprint("analyze_bp", __name__)

# Render/Linux par sirf 'ffmpeg' kaam karta hai
FFMPEG_PATH = "ffmpeg"

# ==========================
# 🎯 NORMALIZE EMOTION
# ==========================
def normalize_emotion(label):
    if not label:
        return "Neutral"
    label = str(label).lower()
    mapping = {
        "fear": "Fearful", "fearful": "Fearful",
        "surprised": "Surprise", "surprise": "Surprise",
        "happy": "Happy", "sad": "Sad",
        "angry": "Angry", "disgust": "Disgust",
        "calm": "Neutral", "neutral": "Neutral"
    }
    return mapping.get(label, label.capitalize())

# ==========================
# 🎤 AUDIO CONVERT
# ==========================
def convert_to_wav(input_path):
    output_path = input_path + ".wav"
    try:
        cmd = [
            FFMPEG_PATH, "-y", "-i", input_path,
            "-ar", "22050", "-ac", "1", output_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            return None
        return output_path if os.path.exists(output_path) else None
    except Exception as e:
        print("❌ Convert Error:", e)
        return None

# ==========================
# 😀 FACE EMOTION
# ==========================
@analyze_bp.route("/face-emotion", methods=["POST"])
def analyze_face():
    # 🔥 LOCAL IMPORT: RAM tabhi use hogi jab function call hoga
    from backend.services.face_emotion import detect_face_emotion
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image provided"}), 400

        file = request.files['image']
        npimg = np.frombuffer(file.read(), np.uint8)
        frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({"error": "Invalid image"}), 400

        label, conf = detect_face_emotion(frame)

        # 🔥 Memory Clean-up
        K.clear_session()
        gc.collect()

        return jsonify({
            "emotion": normalize_emotion(label),
            "confidence": round(min(max(conf * 100, 0), 100), 2)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================
# 🎤 AUDIO + 📝 TEXT
# ==========================
@analyze_bp.route("/analyze-audio-text", methods=["POST"])
def analyze_audio_text():
    # 🔥 LOCAL IMPORTS
    from backend.services.audio_emotion import detect_audio_emotion
    from backend.services.text_emotion import detect_text_emotion
    
    try:
        data = request.get_json(silent=True) or {}
        text = request.form.get("text") or data.get("text")

        if not text:
            return jsonify({"error": "No text provided"}), 400

        original_text = text
        text_lower = text.lower()

        # 🧠 TEXT
        text_label, text_conf = detect_text_emotion(text)
        text_label = normalize_emotion(text_label)
        text_conf = float(text_conf)
        if text_conf <= 1.0: text_conf *= 100
        text_conf = (text_conf * 0.85) + 7
        text_conf = max(0, min(text_conf, 100))

        # 🎤 AUDIO
        audio_label, audio_conf = "no_audio", 0.0
        if 'audio' in request.files:
            audio_file = request.files['audio']
            if audio_file.filename:
                ext = os.path.splitext(audio_file.filename)[-1] or ".webm"
                temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
                wav_path = None
                try:
                    audio_file.save(temp_audio.name)
                    wav_path = convert_to_wav(temp_audio.name) if ext.lower() != ".wav" else temp_audio.name
                    if wav_path:
                        audio_label, audio_conf = detect_audio_emotion(wav_path)
                        audio_label = normalize_emotion(audio_label)
                        audio_conf = float(audio_conf)
                        if audio_conf <= 1.0: audio_conf *= 100
                        audio_conf = (audio_conf * 0.9) + 5
                        audio_conf = max(0, min(audio_conf, 100))
                    else:
                        audio_label, audio_conf = "conversion_failed", 0.0
                finally:
                    temp_audio.close()
                    if os.path.exists(temp_audio.name): os.unlink(temp_audio.name)
                    if wav_path and os.path.exists(wav_path): os.unlink(wav_path)

        # ⚖️ FINAL DECISION
        final_label = text_label
        final_conf = text_conf
        keywords = ["happy", "sad", "angry", "fear", "disgust"]

        if any(k in text_lower for k in keywords):
            final_label = text_label
            final_conf = max(text_conf, 75)
        elif "!" in original_text:
            final_label = "Surprise"
            final_conf = 85
        elif text_conf < 55 and audio_label not in ["no_audio", "Neutral"]:
            final_label = audio_label
            final_conf = audio_conf

        # 🔥 Memory Clean-up
        K.clear_session()
        gc.collect()

        return jsonify({
            "text_emotion": text_label,
            "text_confidence": round(text_conf, 2),
            "audio_emotion": audio_label,
            "audio_confidence": round(audio_conf, 2),
            "final_emotion": normalize_emotion(final_label),
            "final_confidence": round(final_conf, 2)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================
# 🎥 VIDEO + AUDIO (MAIN)
# ==========================
@analyze_bp.route("/analyze-fusion", methods=["POST"])
def analyze_fusion():
    # 🔥 LOCAL IMPORTS
    from backend.services.video_audio_fusion import predict_video
    from backend.services.audio_emotion import detect_audio_emotion

    try:
        if 'video' not in request.files:
            return jsonify({"error": "No video provided"}), 400

        video_file = request.files['video']
        if video_file.filename == "":
            return jsonify({"error": "Empty file"}), 400

        temp_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        audio_path = None

        try:
            video_file.save(temp_video.name)
            # 🎥 VIDEO MODEL
            video_label, video_conf = predict_video(temp_video.name)
            # 🎤 AUDIO EXTRACT
            audio_path = convert_to_wav(temp_video.name)
            if audio_path:
                audio_label, audio_conf = detect_audio_emotion(audio_path)
            else:
                audio_label, audio_conf = "Neutral", 0.0

        finally:
            temp_video.close()
            if os.path.exists(temp_video.name): os.unlink(temp_video.name)
            if audio_path and os.path.exists(audio_path): os.unlink(audio_path)

        # 🔥 FUSION LOGIC
        if audio_conf > video_conf:
            final_label, final_conf = audio_label, audio_conf
        else:
            final_label, final_conf = video_label, video_conf

        # 🔥 Memory Clean-up
        K.clear_session()
        gc.collect()

        return jsonify({
            "emotion": normalize_emotion(final_label),
            "confidence": round(min(max(final_conf, 0), 100), 2)
        })
    except Exception as e:
        print("❌ Fusion Error:", e)
        return jsonify({"error": str(e)}), 500
