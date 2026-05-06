from backend.database.db import db
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # 🔹 BASIC
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # 🔹 PROFILE
    phone = db.Column(db.String(20))
    dob = db.Column(db.Date)   # ✅ FIXED
    gender = db.Column(db.String(10))
    address = db.Column(db.Text)
    bio = db.Column(db.Text)
    profile_pic = db.Column(db.String(200), default="default.png")

    # 🔗 RELATIONSHIP
    history = db.relationship('EmotionHistory', backref='user', lazy=True)

    # 🔐 PASSWORD
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class EmotionHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  
    emotion = db.Column(db.String(50))
    mode = db.Column(db.String(50))