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

# --- Routes ---
@app.route('/')
def index():
    return "<h2>Live Device Location Tracker is Running</h2>"

@app.route('/track')
def track():
    serial = request.args.get('serial')
    return render_template('track.html', serial=serial)

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
    return jsonify({"message": "Location updated", "location": readable_location})

@app.route('/api/location_lookup/<string:serial_number>', methods=['GET'])
def lookup_location(serial_number):
    device = Device.query.filter_by(serial_number=serial_number).first()
    if not device:
        return jsonify({"error": "Device not found"}), 404

    if device.latitude is None or device.longitude is None:
        return jsonify({"error": "No GPS coordinates available"}), 400

    geolocator = Nominatim(user_agent="device_location_lookup")
    location = geolocator.reverse((device.latitude, device.longitude), language='en')

    if not location:
        return jsonify({"error": "Unable to retrieve address"}), 500

    return jsonify({
        "serial_number": serial_number,
        "address": location.address,
        "latitude": device.latitude,
        "longitude": device.longitude,
        "last_updated": device.last_updated.isoformat()
    })

# --- Start Server ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Run on local network to test with phone
    app.run(host='0.0.0.0', port=5000, debug=True)
