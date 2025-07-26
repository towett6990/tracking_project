from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Device {self.serial_number}>'

    def to_dict(self):
        return {
            'id': self.id,
            'serial_number': self.serial_number,
            'make': self.make,
            'model': self.model,
            'device_type': self.device_type,
            'current_status': self.current_status,
            'current_location': self.current_location,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

# --- Run once logic ---
first_request = True

@app.before_request
def run_once():
    global first_request
    if first_request:
        print("Running setup before first request")
        first_request = False

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/devices', methods=['POST'])
def add_device():
    data = request.get_json()
    if not data or not data.get('serial_number'):
        return jsonify({"error": "Serial number is required"}), 400

    if Device.query.filter_by(serial_number=data['serial_number']).first():
        return jsonify({"error": f"Device with serial number {data['serial_number']} already exists"}), 409

    new_device = Device(
        serial_number=data['serial_number'],
        make=data.get('make'),
        model=data.get('model'),
        device_type=data.get('device_type'),
        current_status=data.get('current_status', 'In Stock'),
        current_location=data.get('current_location')
    )
    db.session.add(new_device)
    db.session.commit()
    return jsonify(new_device.to_dict()), 201

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

# --- App Runner ---
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)