# backend/config.py

import os
from dotenv import load_dotenv

# ==============================
# LOAD ENV
# ==============================
load_dotenv()

class Config:

    # ==============================
    # SECURITY
    # ==============================
    SECRET_KEY = os.getenv("SECRET_KEY")

    # ==============================
    # DATABASE
    # ==============================
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ==============================
    # FILES
    # ==============================
    UPLOAD_FOLDER = os.getenv(
        "UPLOAD_FOLDER"
    )

    MAX_CONTENT_LENGTH = int(
        os.getenv(
            "MAX_CONTENT_LENGTH",
            104857600
        )
    )

    # ==============================
    # SESSION
    # ==============================
    SESSION_TIMEOUT = int(
        os.getenv(
            "SESSION_TIMEOUT",
            10
        )
    )

    # ==============================
    # MODELS
    # ==============================
    FACE_MODEL = os.getenv(
        "FACE_MODEL"
    )

    AUDIO_MODEL = os.getenv(
        "AUDIO_MODEL"
    )

    TEXT_MODEL = os.getenv(
        "TEXT_MODEL"
    )

    MULTIMODAL_MODEL = os.getenv(
        "MULTIMODAL_MODEL"
    )
