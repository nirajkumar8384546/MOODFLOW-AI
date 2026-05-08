import os
from datetime import timedelta
from functools import wraps
from flask import Flask, render_template, session, redirect, url_for, jsonify
from flask_migrate import Migrate

# Imports from your project structure
from backend.config import Config
from backend.database.db import db
from backend.database.models import User
from backend.routes.auth_routes import auth_bp
from backend.routes.analyze_routes import analyze_bp
from backend.routes.user_routes import user_bp

# ==============================
# SMART PATH HANDLING (Fixes TemplateNotFound)
# ==============================
# Ye path dhundega ki 'frontend' folder kahan hai
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "frontend", "templates"),
    static_folder=os.path.join(BASE_DIR, "frontend", "static")
)

# ==============================
# CONFIG & DB INIT
# ==============================
app.config.from_object(Config)
app.secret_key = app.config.get("SECRET_KEY", "moodflow_secret_key")
db.init_app(app)
migrate = Migrate(app, db)

# Session management
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=app.config.get("SESSION_TIMEOUT", 30))
app.config["SESSION_PERMANENT"] = True

# ==============================
# AUTO-CREATE DATABASE (Fixes 'no such table' error)
# ==============================
with app.app_context():
    try:
        db.create_all()
        print("✅ Database tables verified/created successfully!")
    except Exception as e:
        print(f"❌ DB Creation Error: {e}")

# ==============================
# LOGIN DECORATOR
# ==============================
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth_bp.login"))
        return f(*args, **kwargs)
    return wrapper

@app.context_processor
def inject_user():
    user = None
    if "user_id" in session:
        user = User.query.get(session["user_id"])
    return dict(current_user=user)

# ==============================
# REGISTER BLUEPRINTS
# ==============================
app.register_blueprint(auth_bp)
app.register_blueprint(analyze_bp)
app.register_blueprint(user_bp)

# ==============================
# ROUTES
# ==============================
@app.route("/")
@app.route("/home")
def dashboard():
    # Login check for home
    if "user_id" not in session and request.path == "/home":
        return redirect(url_for("auth_bp.login"))
    
    images = [f"images/image{i}.png" for i in range(1, 14)]
    return render_template("index.html", images=images)

@app.route("/face")
@login_required
def face_only_emo():
    return render_template("face_only_emo.html")

# Global Error Handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Page not found"}), 404

@app.errorhandler(Exception)
def handle_error(e):
    print(f"❌ CRITICAL ERROR: {e}")
    return jsonify({"error": str(e)}), 500

# Local testing only
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
