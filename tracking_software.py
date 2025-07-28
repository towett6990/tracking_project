from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from geopy.geocoders import Nominatim
import os
from dotenv import load_dotenv
load_dotenv()
# --- App & DB Setup ---
app = Flask(__name__, template_folder=os.path.join(os.getcwd(), 'templates'))
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///devices.db')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
db = SQLAlchemy(app)

# --- Login Manager ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Models ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    serial_number = db.Column(db.String(100), unique=True, nullable=False)
    make = db.Column(db.String(100))
    model = db.Column(db.String(100))
    device_type = db.Column(db.String(100))
    current_status = db.Column(db.String(100), default='In Stock')
    current_location = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

# --- Routes ---
@app.route('/')
def index():
    query = request.args.get('query', '').lower()
    devices = Device.query.all()
    if query:
        devices = [d for d in devices if query in d.serial_number.lower() or
                   query in d.make.lower() or query in d.model.lower() or
                   query in d.device_type.lower() or query in d.current_status.lower() or
                   query in d.current_location.lower()]
    return render_template('index.html', devices=devices)

@app.route('/home')
def home():
    return render_template('landing.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            return "Username already exists", 409
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        return "Invalid credentials", 401
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/add_device', methods=['GET', 'POST'])
@login_required
def add_device():
    if request.method == 'POST':
        serial_number = request.form['serial_number']
        if Device.query.filter_by(serial_number=serial_number).first():
            return "Device with that serial number already exists", 409
        new_device = Device(
            serial_number=serial_number,
            make=request.form['make'],
            model=request.form['model'],
            device_type=request.form['type'],
            current_status=request.form['status'],
            current_location=request.form['location']
        )
        db.session.add(new_device)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_device.html')

@app.route('/track')
@login_required
def track():
    serial = request.args.get('serial')
    return render_template('track.html', serial=serial)

@app.route('/location_lookup_form', methods=['GET', 'POST'])
@login_required
def location_lookup_form():
    latitude = longitude = None
    searched = False
    if request.method == 'POST':
        serial_number = request.form['serial_number']
        device = Device.query.filter_by(serial_number=serial_number).first()
        searched = True
        if device and device.latitude and device.longitude:
            latitude = device.latitude
            longitude = device.longitude
    return render_template('location_lookup_form.html', latitude=latitude, longitude=longitude, searched=searched)

@app.route('/search_device')
@login_required
def search_device():
    serial_number = request.args.get('serial_number', '').strip()
    if serial_number:
        device = Device.query.filter_by(serial_number=serial_number).first()
        return render_template('device_details.html', device=device or None, message="Device not found" if not device else None)
    return redirect(url_for('index'))

# --- API Endpoints ---
@app.route('/api/devices', methods=['GET'])
@login_required
def get_all_devices():
    devices = Device.query.all()
    return jsonify([device.to_dict() for device in devices])

@app.route('/api/devices/<string:serial_number>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def device_crud(serial_number):
    device = Device.query.filter_by(serial_number=serial_number).first()
    if not device:
        return jsonify({"error": "Device not found"}), 404

    if request.method == 'GET':
        return jsonify(device.to_dict())

    elif request.method == 'PUT':
        data = request.get_json()
        device.make = data.get('make', device.make)
        device.model = data.get('model', device.model)
        device.device_type = data.get('device_type', device.device_type)
        device.current_status = data.get('current_status', device.current_status)
        device.current_location = data.get('current_location', device.current_location)
        device.latitude = data.get('latitude', device.latitude)
        device.longitude = data.get('longitude', device.longitude)
        db.session.commit()
        return jsonify(device.to_dict())

    elif request.method == 'DELETE':
        db.session.delete(device)
        db.session.commit()
        return jsonify({"message": "Device deleted successfully"}), 200

@app.route('/api/report_location', methods=['POST'])
def report_location():
    data = request.get_json()
    serial_number = data.get('serial_number')
    device = Device.query.filter_by(serial_number=serial_number).first()
    if not device:
        return jsonify({"error": "Device not found"}), 404
    device.latitude = data.get('latitude', device.latitude)
    device.longitude = data.get('longitude', device.longitude)
    device.current_location = data.get('current_location', device.current_location)
    db.session.commit()
    return jsonify({"message": "Location updated successfully"})

@app.route('/api/location_lookup/<string:serial_number>', methods=['GET'])
@login_required
def lookup_location(serial_number):
    device = Device.query.filter_by(serial_number=serial_number).first()
    if not device:
        return jsonify({"error": "Device not found"}), 404

    if device.latitude is None or device.longitude is None:
        return jsonify({"error": "No coordinates available for this device"}), 400

    geolocator = Nominatim(user_agent="device_location_lookup")
    location = geolocator.reverse((device.latitude, device.longitude), language='en')
    if not location:
        return jsonify({"error": "Could not find address"}), 500

    return jsonify({
        "serial_number": serial_number,
        "address": location.address,
        "latitude": device.latitude,
        "longitude": device.longitude
    })
@app.route('/report')
def report():
    return render_template('report_location.html')

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
