# app.py

import os
from datetime import timedelta
from functools import wraps

from flask import (
    Flask,
    render_template,
    session,
    redirect,
    url_for,
    jsonify
)

from flask_migrate import Migrate

from backend.config import Config
from backend.database.db import db
from backend.database.models import User

from backend.routes.auth_routes import auth_bp
from backend.routes.analyze_routes import analyze_bp
from backend.routes.user_routes import user_bp

# ==============================
# BASE PATH
# ==============================
BASE_DIR = os.path.abspath(
    os.path.dirname(__file__)
)

ROOT_DIR = os.path.abspath(
    os.path.join(BASE_DIR, "..")
)

# ==============================
# APP INIT
# ==============================
app = Flask(
    __name__,
    template_folder=os.path.join(
        ROOT_DIR,
        "frontend/templates"
    ),
    static_folder=os.path.join(
        ROOT_DIR,
        "frontend/static"
    )
)

# ==============================
# LOAD CONFIG
# ==============================
app.config.from_object(Config)

# ==============================
# SECRET KEY
# ==============================
app.secret_key = app.config["SECRET_KEY"]

# ==============================
# UPLOAD FOLDER
# ==============================
UPLOAD_FOLDER = os.path.join(
    ROOT_DIR,
    app.config["UPLOAD_FOLDER"]
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ==============================
# DATABASE INIT
# ==============================
db.init_app(app)

# ==============================
# SESSION CONFIG
# ==============================
app.config[
    "PERMANENT_SESSION_LIFETIME"
] = timedelta(
    minutes=app.config["SESSION_TIMEOUT"]
)

app.config["SESSION_PERMANENT"] = True

# ==============================
# MIGRATION
# ==============================
migrate = Migrate(app, db)

# ==============================
# LOGIN DECORATOR
# ==============================
def login_required(f):

    @wraps(f)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:

            return redirect(
                url_for("auth_bp.login")
            )

        return f(*args, **kwargs)

    return wrapper

# ==============================
# GLOBAL USER
# ==============================
@app.context_processor
def inject_user():

    if "user_id" in session:

        user = User.query.get(
            session["user_id"]
        )

        return dict(current_user=user)

    return dict(current_user=None)

# ==============================
# REGISTER BLUEPRINTS
# ==============================
app.register_blueprint(auth_bp)
app.register_blueprint(analyze_bp)
app.register_blueprint(user_bp)

# ==============================
# PUBLIC PAGE
# ==============================
@app.route("/")
def dashboard():

    images = [
        f"images/image{i}.png"
        for i in range(1, 14)
    ]

    return render_template(
        "index.html",
        images=images
    )

# ==============================
# HOME
# ==============================
@app.route("/home")
@login_required
def home():

    images = [
        f"images/image{i}.png"
        for i in range(1, 14)
    ]

    return render_template(
        "index.html",
        images=images
    )

# ==============================
# FACE PAGE
# ==============================
@app.route("/face")
@login_required
def face_only_emo():

    return render_template(
        "face_only_emo.html"
    )

# ==============================
# AUDIO + TEXT PAGE
# ==============================
@app.route("/audio-text")
@login_required
def audio_text():

    return render_template(
        "audio+text_emo.html"
    )

# ==============================
# VIDEO + AUDIO PAGE
# ==============================
@app.route("/video-audio")
@login_required
def video_audio():

    return render_template(
        "video+audio_emo.html"
    )

# ==============================
# MOOD HISTORY
# ==============================
@app.route("/mood-history")
@login_required
def mood_history():

    return render_template(
        "mood_history.html"
    )

# ==============================
# ABOUT PAGE
# ==============================
@app.route("/about")
@login_required
def about():

    return render_template(
        "about.html"
    )

# ==============================
# LOGIN CHECK API
# ==============================
@app.route("/auth/check-login")
def check_login():

    return jsonify({
        "logged_in":
        "user_id" in session
    })

# ==============================
# FILE TOO LARGE
# ==============================
@app.errorhandler(413)
def too_large(e):

    return jsonify({
        "error":
        "File too large (max 100MB)"
    }), 413

# ==============================
# GLOBAL ERROR
# ==============================
@app.errorhandler(Exception)
def handle_error(e):

    print("❌ ERROR:", e)

    return jsonify({
        "error": str(e)
    }), 500
with app.app_context():
    db.create_all()
    print("✅ Database tables created successfully!")
# ==============================
# RUN
# ==============================
if __name__ == "__main__":

    app.run(
        host=os.getenv(
            "HOST",
            "127.0.0.1"
        ),

        port=int(
            os.getenv(
                "PORT",
                5000
            )
        ),

        debug=os.getenv(
            "FLASK_ENV"
        ) == "development"
    )
