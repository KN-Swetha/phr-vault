from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize SQLAlchemy
db = SQLAlchemy()

# -----------------------------
# User model
# -----------------------------
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    profile = db.relationship("UserProfile", back_populates="user", uselist=False)
    records = db.relationship("HealthRecord", back_populates="user", cascade="all, delete-orphan")

    # Password methods
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# -----------------------------
# User profile model
# -----------------------------
class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    blood_group = db.Column(db.String(10))
    known_conditions = db.Column(db.Text)
    address = db.Column(db.Text)

    user = db.relationship("User", back_populates="profile")

# -----------------------------
# Health record model
# -----------------------------
class HealthRecord(db.Model):
    __tablename__ = "health_records"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    filename = db.Column(db.String(300), nullable=False)  # saved filename
    original_filename = db.Column(db.String(300), nullable=False)  # original name
    file_type = db.Column(db.String(50))  # Prescription/Lab/Scan/...
    doctor_name = db.Column(db.String(200))
    hospital_name = db.Column(db.String(200))
    visit_date = db.Column(db.Date)  # date of visit / report
    notes = db.Column(db.Text)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="records")
