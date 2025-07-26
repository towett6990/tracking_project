from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from geopy.geocoders import Nominatim

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///devices.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Database Model ---
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

# --- Web Routes ---
@app.route('/')
def index():
    query = request.args.get('query', '').lower()
    devices = Device.query.all()

    if query:
        devices = [d for d in devices if 
                   query in d.serial_number.lower() or
                   query in d.make.lower() or
                   query in d.model.lower() or
                   query in d.device_type.lower() or
                   query in d.current_status.lower() or
                   query in d.current_location.lower()
        ]
    return render_template('index.html', devices=devices)

@app.route('/add_device', methods=['GET', 'POST'])
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
def track():
    serial = request.args.get('serial')
    return render_template('track.html', serial=serial)

# ✅ New Route for Location Lookup Form
@app.route('/location_lookup_form')
def location_lookup_form():
    return render_template('location_lookup.html')

# --- API Routes ---
@app.route('/api/devices', methods=['GET'])
def get_all_devices():
    devices = Device.query.all()
    return jsonify([device.to_dict() for device in devices])

@app.route('/api/devices/<string:serial_number>', methods=['GET'])
def get_device_by_serial(serial_number):
    device = Device.query.filter_by(serial_number=serial_number).first()
    if device:
        return jsonify(device.to_dict())
    return jsonify({"error": "Device not found"}), 404

@app.route('/api/devices/<string:serial_number>', methods=['PUT'])
def update_device(serial_number):
    data = request.get_json()
    device = Device.query.filter_by(serial_number=serial_number).first()
    if not device:
        return jsonify({"error": "Device not found"}), 404

    device.make = data.get('make', device.make)
    device.model = data.get('model', device.model)
    device.device_type = data.get('device_type', device.device_type)
    device.current_status = data.get('current_status', device.current_status)
    device.current_location = data.get('current_location', device.current_location)
    device.latitude = data.get('latitude', device.latitude)
    device.longitude = data.get('longitude', device.longitude)
    db.session.commit()
    return jsonify(device.to_dict())

@app.route('/api/devices/<string:serial_number>', methods=['DELETE'])
def delete_device(serial_number):
    device = Device.query.filter_by(serial_number=serial_number).first()
    if not device:
        return jsonify({"error": "Device not found"}), 404
    db.session.delete(device)
    db.session.commit()
    return jsonify({"message": "Device deleted successfully"}), 200

@app.route('/api/report_location', methods=['POST'])
def report_location():
    data = request.get_json()
    serial_number = data.get("serial_number")
    lat = data.get("latitude")
    lon = data.get("longitude")

    device = Device.query.filter_by(serial_number=serial_number).first()
    if not device:
        return jsonify({"error": "Device not found"}), 404

    geolocator = Nominatim(user_agent="device_tracker")
    location = geolocator.reverse(f"{lat}, {lon}", language='en')
    readable_location = location.address if location else f"Lat: {lat:.6f}, Lon: {lon:.6f}"

    device.latitude = lat
    device.longitude = lon
    device.current_location = readable_location
    db.session.commit()
    return jsonify({"message": "Location updated successfully", "location": readable_location})

@app.route('/api/location_lookup/<string:serial_number>', methods=['GET'])
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
        "longitude": device.longitude,
        "last_updated": device.last_updated.isoformat()
    })

# --- App Runner ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
