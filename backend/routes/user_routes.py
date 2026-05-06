# user_routes.py

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from backend.database.models import User
from backend.database.db import db
from datetime import datetime
import os
import uuid

user_bp = Blueprint("user_bp", __name__, url_prefix="/user")


# ==========================
# 👤 PROFILE PAGE
# ==========================
@user_bp.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect(url_for("auth_bp.login"))

    user = User.query.get(session["user_id"])

    return render_template("profile.html", user=user)


# ==========================
# 🔄 UPDATE PROFILE
# ==========================
@user_bp.route("/update-profile", methods=["GET", "POST"])
def update_profile():

    if "user_id" not in session:
        return redirect(url_for("auth_bp.login"))

    user = User.query.get(session["user_id"])

    if request.method == "POST":
        try:
            # ==========================
            # ✅ BASIC DATA
            # ==========================
            user.username = request.form.get("username", "").strip()
            user.email = request.form.get("email", "").strip()
            user.phone = request.form.get("phone", "").strip()

            # ==========================
            # ✅ DOB FIX (SAFE)
            # ==========================
            dob_str = request.form.get("dob")

            if dob_str:
                try:
                    user.dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
                except Exception:
                    user.dob = None
            else:
                user.dob = None

            # ==========================
            # ✅ OTHER FIELDS
            # ==========================
            user.gender = request.form.get("gender", "")
            user.address = request.form.get("address", "").strip()
            user.bio = request.form.get("bio", "").strip()

            # ==========================
            # 📸 PROFILE PIC UPLOAD (ADVANCED FIX)
            # ==========================
            if "profile_pic" in request.files:
                file = request.files["profile_pic"]

                if file and file.filename:
                    upload_path = current_app.config["UPLOAD_FOLDER"]
                    os.makedirs(upload_path, exist_ok=True)

                    # 🔒 SAFE EXTENSION
                    ext = file.filename.rsplit(".", 1)[-1].lower()
                    allowed = ["jpg", "jpeg", "png", "webp"]

                    if ext not in allowed:
                        flash("Only image files allowed ❌")
                        return redirect(request.url)

                    # 🆕 UNIQUE NAME
                    filename = f"{uuid.uuid4().hex}.{ext}"
                    file_path = os.path.join(upload_path, filename)

                    # 🧹 DELETE OLD IMAGE (optional but pro)
                    if user.profile_pic and user.profile_pic != "default.png":
                        old_path = os.path.join(upload_path, user.profile_pic)
                        if os.path.exists(old_path):
                            try:
                                os.remove(old_path)
                            except:
                                pass

                    # 💾 SAVE NEW IMAGE
                    file.save(file_path)
                    user.profile_pic = filename

            # ==========================
            # 💾 SAVE
            # ==========================
            db.session.commit()

            # update session
            session["username"] = user.username

            flash("Profile updated successfully ✅")

            return redirect(url_for("user_bp.profile"))

        except Exception as e:
            db.session.rollback()   # 🔥 MUST
            print("❌ Update Error:", e)
            flash("Update failed ❌")

    return render_template("update_profile.html", user=user)