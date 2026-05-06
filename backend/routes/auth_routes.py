from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from backend.database.models import User
from backend.database.db import db

# 🔥 ADDED (session lifetime support ke liye safe import)
from datetime import timedelta

auth_bp = Blueprint("auth_bp", __name__, url_prefix="/auth")


# ==========================
# REGISTER
# ==========================
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        # 🔍 check existing
        if User.query.filter_by(email=email).first():
            flash("Email already registered ❌")
            return redirect(url_for("auth_bp.register"))

        # ✅ create user
        new_user = User(username=username, email=email)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful ✅ Please login")
        return redirect(url_for("auth_bp.login"))

    return render_template("register.html")


# ==========================
# LOGIN 
# ==========================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    # 🔥 ADDED: agar already logged in hai to home bhejo
    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            # ✅ SESSION SET
            session.permanent = True   # 🔥 required for timeout support
            session["user_id"] = user.id
            session["username"] = user.username

            flash("Login successful 🎉")
            return redirect(url_for("home"))

        else:
            flash("Invalid Email or Password ❌")
            return redirect(url_for("auth_bp.login"))

    return render_template("login.html")


# ==========================
# LOGOUT
# ==========================
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully 👋")
    return redirect(url_for("auth_bp.login"))