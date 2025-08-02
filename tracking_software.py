from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# =========================
# CONFIG
# =========================
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///devices.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# =========================
# INIT
# =========================
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# =========================
# MODELS
# =========================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # ✅ Relationship
    devices = db.relationship('Device', backref='user', lazy=True)

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    serial_number = db.Column(db.String(100), nullable=False)
    make = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    device_type = db.Column(db.String(100), nullable=False)
    current_status = db.Column(db.String(100), nullable=False)
    current_location = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'serial_number': self.serial_number,
            'make': self.make,
            'model': self.model,
            'device_type': self.device_type,
            'current_status': self.current_status,
            'current_location': self.current_location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

class DeviceLocationHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    serial_number = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# =========================
# LOGIN SETUP
# =========================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# =========================
# ROUTES
# =========================
@app.route('/')
@login_required
def index():
    query = request.args.get('query', '').lower()
    devices = Device.query.filter_by(user_id=current_user.id).all()
    if query:
        devices = [d for d in devices if query in d.serial_number.lower() or
                   query in d.make.lower() or query in d.model.lower() or
                   query in d.device_type.lower() or query in d.current_status.lower() or
                   query in d.current_location.lower()]
    return render_template('index.html', devices=devices)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists.')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. You can now log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/add_device', methods=['GET', 'POST'])
@login_required
def add_device():
    if request.method == 'POST':
        serial_number = request.form['serial_number']
        existing_device = Device.query.filter_by(serial_number=serial_number, user_id=current_user.id).first()
        if existing_device:
            flash('Device with that serial number already exists.')
            return redirect(url_for('add_device'))

        new_device = Device(
            serial_number=serial_number,
            make=request.form['make'],
            model=request.form['model'],
            device_type=request.form['type'],
            current_status=request.form['status'],
            current_location=request.form['location'],
            user_id=current_user.id
        )
        db.session.add(new_device)
        db.session.commit()
        flash('Device added successfully.')
        return redirect(url_for('index'))

    return render_template('add_device.html')

@app.route('/search_device', methods=['POST'])
@login_required
def search_device():
    serial_number = request.form['serial_number']
    device = Device.query.filter_by(serial_number=serial_number, user_id=current_user.id).first()
    return render_template('search_results.html', device=device)
@app.route('/map')
@login_required
def map_view():
    devices = Device.query.filter_by(user_id=current_user.id).all()
    return render_template('map.html', devices=devices)

# =========================
# API ROUTES
# =========================
@app.route('/api/devices', methods=['GET'])
@login_required
def get_devices():
    devices = Device.query.filter_by(user_id=current_user.id).all()
    return jsonify([device.to_dict() for device in devices])

@app.route('/api/device-serials')
@login_required
def device_serials():
    devices = Device.query.filter_by(user_id=current_user.id).with_entities(Device.serial_number).all()
    return jsonify([d.serial_number for d in devices])

@app.route('/api/devices/<serial_number>', methods=['GET'])
@login_required
def get_device_by_serial(serial_number):
    device = Device.query.filter_by(serial_number=serial_number, user_id=current_user.id).first()
    if device:
        return jsonify(device.to_dict())
    return jsonify({'error': 'Device not found'}), 404

@app.route('/api/devices/<serial_number>/history', methods=['GET'])
@login_required
def device_history(serial_number):
    history = DeviceLocationHistory.query.filter_by(serial_number=serial_number).order_by(DeviceLocationHistory.timestamp).all()
    return jsonify([
        {'latitude': h.latitude, 'longitude': h.longitude}
        for h in history
    ])

@app.route('/api/report_location', methods=['POST'])
def report_location():
    data = request.get_json()
    serial_number = data.get('serial_number')
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    device = Device.query.filter_by(serial_number=serial_number).first()
    if not device:
        return jsonify({'error': 'Device not found'}), 404

    device.latitude = latitude
    device.longitude = longitude
    device.last_updated = datetime.utcnow()

    history = DeviceLocationHistory(
        serial_number=serial_number,
        latitude=latitude,
        longitude=longitude
    )

    db.session.add(history)
    db.session.commit()
    return jsonify({'message': 'Location updated and history recorded'})

@app.route('/api/location_lookup/<serial_number>', methods=['GET'])
@login_required
def location_lookup(serial_number):
    device = Device.query.filter_by(serial_number=serial_number, user_id=current_user.id).first()
    if device:
        return jsonify({
            'latitude': device.latitude,
            'longitude': device.longitude,
            'last_updated': device.last_updated.isoformat() if device.last_updated else None
        })
    return jsonify({'error': 'Device not found'}), 404

# =========================
# RUN
# =========================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))  # Use PORT from environment or fallback to 5000
    app.run(host='0.0.0.0', port=port, debug=True)