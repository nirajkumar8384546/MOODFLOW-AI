# app.py
import os
from flask import Flask, render_template, session, redirect, url_for, jsonify
from backend.database.db import db
from backend.routes.auth_routes import auth_bp
from backend.routes.analyze_routes import analyze_bp
from backend.routes.user_routes import user_bp
from backend.database.models import User
from datetime import timedelta

# ==============================
# BASE PATH
# ==============================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))

# ==============================
# APP INIT
# ==============================
app = Flask(
    __name__,
    template_folder=os.path.join(ROOT_DIR, "frontend/templates"),
    static_folder=os.path.join(ROOT_DIR, "frontend/static")
)

# ==============================
# SECURITY
# ==============================
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

# ==============================
# FILE SIZE LIMIT
# ==============================
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

# ==============================
# UPLOAD FOLDER
# ==============================
UPLOAD_FOLDER = os.path.join(ROOT_DIR, "frontend/static/uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ==============================
# DATABASE CONFIG
# ==============================
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(ROOT_DIR, "moodflow.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=10)
app.config["SESSION_PERMANENT"] = True
# ==============================
# MIGRATION
# ==============================
from flask_migrate import Migrate
migrate = Migrate(app, db)

# ==============================
# LOGIN DECORATOR (ADDED FIX)
# ==============================
from functools import wraps

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth_bp.login"))
        return f(*args, **kwargs)
    return wrapper


# ==============================
# GLOBAL USER
# ==============================
@app.context_processor
def inject_user():
    if "user_id" in session:
        user = User.query.get(session["user_id"])
        return dict(current_user=user)
    return dict(current_user=None)


# ==============================
# REGISTER BLUEPRINTS
# ==============================
app.register_blueprint(auth_bp)
app.register_blueprint(analyze_bp)
app.register_blueprint(user_bp)


# ==============================
# AUTH CHECK
# ==============================
def check_auth():
    return "user_id" in session


# ==============================
# PUBLIC PAGE
# ==============================
@app.route("/")
def dashboard():
    images = [f"images/image{i}.png" for i in range(1, 14)]
    return render_template("index.html", images=images)


# ==============================
# PROTECTED HOME
# ==============================
@app.route("/home")
@login_required
def home():
    images = [f"images/image{i}.png" for i in range(1, 14)]
    return render_template("index.html", images=images)


# ==============================
# PROTECTED PAGES
# ==============================
@app.route("/face")
@login_required
def face_only_emo():
    return render_template("face_only_emo.html")


@app.route("/audio-text")
@login_required
def audio_text():
    return render_template("audio+text_emo.html")


@app.route("/video-audio")
@login_required
def video_audio():
    return render_template("video+audio_emo.html")


# ==============================
# ERROR HANDLERS
# ==============================
@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large (max 100MB)"}), 413


@app.errorhandler(Exception)
def handle_error(e):
    print("❌ ERROR:", e)
    return jsonify({"error": str(e)}), 500


# ==============================
# MOOD HISTORY PAGE
# ==============================
@app.route("/mood-history")
@login_required
def mood_history():
    return render_template("mood_history.html")


# ==============================
# API - GET MOODS
# ==============================
@app.route("/api/moods")
def get_moods():
    import sqlite3

    conn = sqlite3.connect(os.path.join(ROOT_DIR, "moodflow.db"))
    c = conn.cursor()

    c.execute("SELECT emotion, timestamp FROM moods ORDER BY id DESC LIMIT 50")
    data = c.fetchall()

    conn.close()

    return jsonify([
        {"emotion": d[0], "time": d[1]} for d in data
    ])


# ==============================
# AI INSIGHTS
# ==============================
@app.route("/api/insights")
def insights():
    import sqlite3
    from collections import Counter

    conn = sqlite3.connect(os.path.join(ROOT_DIR, "moodflow.db"))
    c = conn.cursor()

    c.execute("SELECT emotion FROM moods")
    data = [d[0] for d in c.fetchall()]

    conn.close()

    if not data:
        return jsonify({"insight": "No data yet"})

    count = Counter(data)
    most = count.most_common(1)[0][0]

    return jsonify({
        "insight": f"You are mostly feeling {most} lately"
    })


# ==============================
# FILTERED DATA
# ==============================
@app.route("/api/moods/filter")
def filter_moods():
    import sqlite3
    from datetime import datetime, timedelta
    from flask import request

    filter_type = request.args.get("type")
    start = request.args.get("start")
    end = request.args.get("end")

    conn = sqlite3.connect(os.path.join(ROOT_DIR, "moodflow.db"))
    c = conn.cursor()

    query = "SELECT emotion, timestamp FROM moods WHERE 1=1"
    params = []

    if filter_type == "daily":
        today = datetime.now().strftime("%Y-%m-%d")
        query += " AND timestamp LIKE ?"
        params.append(f"{today}%")

    elif filter_type == "weekly":
        date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        query += " AND timestamp >= ?"
        params.append(date)

    elif filter_type == "monthly":
        date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        query += " AND timestamp >= ?"
        params.append(date)

    elif filter_type == "custom" and start and end:
        query += " AND DATE(timestamp) BETWEEN ? AND ?"
        params.extend([start, end])

    c.execute(query, params)
    data = c.fetchall()
    conn.close()

    return jsonify([
        {"emotion": d[0], "time": d[1]} for d in data
    ])


# ==============================
# CONTACT
# ==============================
@app.route("/contact", methods=["GET", "POST"])
def contact():
    from flask import request
    import sqlite3
    from datetime import datetime

    if request.method == "GET":
        return render_template("contact.html")

    data = request.get_json()

    conn = sqlite3.connect(os.path.join(ROOT_DIR, "moodflow.db"))
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS contact (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            message TEXT,
            timestamp TEXT
        )
    """)

    c.execute("""
        INSERT INTO contact (name, email, message, timestamp)
        VALUES (?, ?, ?, ?)
    """, (data["name"], data["email"], data["message"], datetime.now()))

    conn.commit()
    conn.close()

    return {"msg": "Message sent successfully ✅"}


# ==============================
# ABOUT
# ==============================
@app.route("/about")
@login_required
def about():
    return render_template("about.html")


# ==============================
# 🔥 NEW: LOGIN CHECK API (ADDED)
# ==============================
@app.route("/auth/check-login")
def check_login():
    return jsonify({
        "logged_in": "user_id" in session
    })


# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    app.run(debug=False)