from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# -------------------
# User Model
# -------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(256), nullable=False)
    plan = db.Column(db.String(20), default="free")  # free or pro

    devices = db.relationship("Device", backref="owner", lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"


# -------------------
# Device Model
# -----------
class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    serial_number = db.Column(db.String(100), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    make = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    device_type = db.Column(db.String(50), nullable=True)
    os_version = db.Column(db.String(50), nullable=True)
    current_status = db.Column(db.String(20), nullable=False, default="active")
    current_location = db.Column(db.String(100), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, nullable=True)


    def __repr__(self):
        return f"<Device {self.name} ({self.serial_number})>"
