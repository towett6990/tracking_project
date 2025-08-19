from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from flask_login import LoginManager, current_user
import os
import json
import stripe
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret')

# Detect if DATABASE_URL is set (Render will set it)
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Fix old-style postgres:// to postgresql://
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace("postgres://", "postgresql://", 1)
else:
    # Local SQLite setup
    instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    os.makedirs(instance_path, exist_ok=True)
    db_path = os.path.join(instance_path, 'devices.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@app.context_processor
def inject_user_and_year():
    from flask_login import current_user
    from datetime import datetime
    return dict(current_user=current_user, current_year=datetime.now().year)


# ===================== MODELS =====================
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(256), nullable=False)
    plan = db.Column(db.String(20), default="free")  # "free", "basic", "pro"


class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    serial_number = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    make = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    device_type = db.Column(db.String(100), nullable=False)
    current_status = db.Column(db.String(100), nullable=False)
    current_location = db.Column(db.String(100), nullable=False)
    os_version = db.Column(db.String(100))   # ✅ NEW FIELD
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    last_updated = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    last_seen = db.Column(db.DateTime)



    def to_dict(self):
        return {
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
    serial_number = db.Column(db.String(100), nullable=False, index=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class DeviceCommand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    serial_number = db.Column(db.String(100), nullable=False)
    command_type = db.Column(db.String(50), nullable=False)
    command_data = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    executed_at = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

# ===================== LOGIN =====================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ===================== ROUTES =====================
@app.route('/')
@login_required
def index():
    query = request.args.get('query', '').lower()
    devices = Device.query.filter_by(user_id=current_user.id).all()
    if query:
        devices = [d for d in devices if query in d.serial_number.lower()]
    return render_template('index.html', devices=devices)

import csv
from flask import Response

@app.route('/export/<serial_number>', methods=['GET'])
@login_required
def export_device_history(serial_number):
    # Fetch device to confirm user owns it
    device = Device.query.filter_by(serial_number=serial_number, user_id=current_user.id).first()
    if not device:
        return jsonify({'error': 'Device not found or access denied'}), 404

    # Fetch location history
    history = DeviceLocationHistory.query.filter_by(serial_number=serial_number).order_by(DeviceLocationHistory.timestamp).all()

    # Create CSV response
    def generate():
        yield 'Serial Number,Latitude,Longitude,Timestamp\n'
        for entry in history:
            yield f"{entry.serial_number},{entry.latitude},{entry.longitude},{entry.timestamp}\n"

    return Response(generate(), mimetype='text/csv',
                    headers={"Content-Disposition": f"attachment;filename={serial_number}_history.csv"})


stripe.api_key = os.getenv("STRIPE_SECRET_KEY") or "your_test_key_here"

@app.route("/checkout/<plan>")
@login_required
def checkout(plan):
    try:
        if plan == "basic":
            price = 200  # KES 200
        elif plan == "pro":
            price = 500  # KES 500
        else:
            flash("Invalid plan")
            return redirect(url_for("pricing"))

        # Create Stripe Checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "kes",  # or "usd"
                    "product_data": {"name": f"{plan.capitalize()} Plan"},
                    "unit_amount": price * 100,  # Stripe uses cents
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=url_for("payment_success", plan=plan, _external=True),
            cancel_url=url_for("pricing", _external=True),
        )

        return redirect(session.url, code=303)

    except Exception as e:
        return str(e), 400


@app.route("/payment_success/<plan>")
@login_required
def payment_success(plan):
    current_user.plan = plan
    db.session.commit()
    flash(f"✅ Payment successful! You are now on the {plan.capitalize()} Plan.")
    return redirect(url_for("dashboard"))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('User already exists')
            return redirect(url_for('register'))
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route("/live_map/<serial_number>")
@login_required
def live_map(serial_number):
    device = Device.query.filter_by(serial_number=serial_number).first_or_404()
    return render_template("live_map.html", device=device)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid credentials')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/edit_device/<int:device_id>', methods=['GET', 'POST'])
@login_required
def edit_device(device_id):
    device = Device.query.get_or_404(device_id)
    if device.user_id != current_user.id:
        flash("Unauthorized access.")
        return redirect(url_for('index'))

    if request.method == 'POST':
        device.make = request.form['make']
        device.model = request.form['model']
        device.device_type = request.form['type']
        device.current_status = request.form['status']
        device.current_location = request.form['location']
        db.session.commit()
        flash("Device updated.")
        return redirect(url_for('index'))

    return render_template('edit_device.html', device=device)

@app.route("/api/register_device", methods=["POST"])
def api_register_device():
    data = request.json
    try:
        serial_number = data.get("serial_number")
        name = data.get("name")
        make = data.get("make")
        model = data.get("model")
        device_type = data.get("device_type")
        current_status = data.get("current_status")
        current_location = data.get("current_location")
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        user_id = data.get("user_id")

        timestamp = datetime.now(timezone.utc)

        new_device = Device(
            serial_number=serial_number,
            name=name,
            make=make,
            model=model,
            device_type=device_type,
            current_status=current_status,
            current_location=current_location,
            latitude=latitude,
            longitude=longitude,
            user_id=user_id,
            last_seen=timestamp
        )

        db.session.add(new_device)
        db.session.commit()

        return jsonify({"message": "Device registered successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


    # Create new device
    new_device = Device(
        serial_number=serial_number,
        make=make,
        model=model,
        device_type=device_type,
        os_version=os_version,
        app_version=app_version,
        last_seen=timestamp
    )
    db.session.add(new_device)
    db.session.commit()
    return jsonify({"message": "Device registered successfully"}), 201


@app.route('/delete_device/<int:device_id>', methods=['POST'])
@login_required
def delete_device(device_id):
    device = Device.query.get_or_404(device_id)
    if device.user_id != current_user.id:
        flash("Unauthorized access.")
        return redirect(url_for('index'))

    db.session.delete(device)
    db.session.commit()
    flash("Device deleted.")
    return redirect(url_for('index'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/add_device", methods=["GET", "POST"])
@login_required
def add_device():
    device_limit = {
        "free": 1,
        "basic": 5,
        "pro": None  # unlimited
    }

    current_devices = Device.query.filter_by(user_id=current_user.id).count()
    limit = device_limit.get(current_user.plan)

    if limit is not None and current_devices >= limit:
        flash(f"⚠️ Your {current_user.plan.capitalize()} Plan allows only {limit} devices. Upgrade for more!")
        return redirect(url_for("dashboard"))

    if request.method == 'POST':
        serial_number = request.form.get('serial_number')
        name = request.form.get('name')  # ✅ Get device name
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')

        new_device = Device(
            serial_number=serial_number,
            name=name,
            latitude=latitude,
            longitude=longitude
        )
        db.session.add(new_device)
        db.session.commit()
        flash('Device added successfully', 'success')
        return redirect(url_for('device_list'))
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

# ===================== API ROUTES =====================
@app.route('/api/devices')
@login_required
def api_devices():
    devices = Device.query.all()

    def get_status(device):
        if device.last_seen:
            if datetime.now(timezone.utc) - device.last_seen <= timedelta(minutes=5):
                return "online"
        return "offline"

    devices_data = []
    for d in devices:
        devices_data.append({
            "id": d.id,
            "name": d.name,
            "serial_number": d.serial_number,
            "latitude": d.latitude,
            "longitude": d.longitude,
            "last_seen": d.last_seen.isoformat() if d.last_seen else None,
            "status": get_status(d)
        })

    return jsonify(devices_data)


@app.route("/api/report_location", methods=["POST"])
def api_report_location():
    data = request.json
    serial_number = data.get("serial_number")
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    last_seen = data.get("last_seen")
    current_location = data.get("current_location")
    current_status = data.get("current_status")

    device = Device.query.filter_by(serial_number=serial_number).first()
    if device:
        device.latitude = latitude
        device.longitude = longitude
        device.last_seen = datetime.fromisoformat(last_seen)
        device.current_location = current_location
        device.current_status = current_status
        db.session.commit()
        return jsonify({"message": "Location updated"}), 200
    else:
        return jsonify({"error": "Device not found"}), 404



@app.route('/api/live_locations')
def live_locations():
    devices = Device.query.all()
    data = [
        {
            'serial_number': d.serial_number,
            'latitude': d.latitude,
            'longitude': d.longitude,
            'last_seen': d.last_seen.strftime('%Y-%m-%d %H:%M:%S') if d.last_seen else None
        }
        for d in devices
        if d.latitude is not None and d.longitude is not None
    ]
    return jsonify(data)

@app.route("/api/all_devices")
def all_devices():
    devices = Device.query.all()
    data = []
    for d in devices:
        if d.latitude is not None and d.longitude is not None:
            data.append({
                "serial_number": d.serial_number,
                "latitude": d.latitude,
                "longitude": d.longitude,
                "last_seen": d.last_seen.isoformat() if d.last_seen else None
            })
    return jsonify(data)


@app.route('/api/send_command', methods=['POST'])
@login_required
def send_command():
    data = request.get_json()
    device = Device.query.filter_by(serial_number=data.get('serial_number'), user_id=current_user.id).first()
    if not device:
        return jsonify({'error': 'Device not found'}), 404
    command = DeviceCommand(
        serial_number=data.get('serial_number'),
        command_type=data.get('command_type'),
        command_data=json.dumps(data.get('command_data', {})),
        user_id=current_user.id
    )
    db.session.add(command)
    db.session.commit()
    return jsonify({'message': 'Command sent', 'command_id': command.id})

@app.route('/api/device_commands/<serial_number>', methods=['GET'])
def get_device_commands(serial_number):
    commands = DeviceCommand.query.filter_by(serial_number=serial_number, status='pending').all()
    result = []
    for cmd in commands:
        result.append({
            'id': cmd.id,
            'type': cmd.command_type,
            'data': json.loads(cmd.command_data or '{}'),
            'created_at': cmd.created_at.isoformat()
        })
        cmd.status = 'sent'
    db.session.commit()
    return jsonify(result)
@app.route('/lost_device', methods=['GET', 'POST'])
def lost_device():
    if request.method == 'POST':
        serial_number = request.form.get('serial_number')
        device = Device.query.filter_by(serial_number=serial_number).first()
        if device and device.latitude and device.longitude:
            location = {
                'serial_number': device.serial_number,
                'last_seen': device.last_seen,
                'latitude': device.latitude,
                'longitude': device.longitude
            }
            return render_template('lost_device.html', location=location)
        else:
            flash('Device not found or not registered.')
    return render_template('lost_device.html')

@app.route("/pricing")
def pricing():
    return render_template("pricing.html")


@app.route('/api/device_location/<serial_number>', methods=['GET'])
def get_device_location(serial_number):
    device = Device.query.filter_by(serial_number=serial_number).first()
    if device and device.latitude and device.longitude:
        return jsonify({
            'latitude': device.latitude,
            'longitude': device.longitude,
            'last_seen': device.last_seen.isoformat() if device.last_seen else None
        })
    return jsonify({'error': 'Device not found'}), 404

@app.route("/dashboard")
@login_required
def dashboard():
    devices = Device.query.filter_by(user_id=current_user.id).all()
    return render_template("dashboard.html", user=current_user, devices=devices)


@app.route('/api/command_ack', methods=['POST'])
def command_ack():
    data = request.get_json()
    cmd = DeviceCommand.query.get(data.get('command_id'))
    if not cmd:
        return jsonify({'error': 'Command not found'}), 404
    cmd.status = data.get('status', 'executed')
    cmd.executed_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({'message': 'Command acknowledged'})
@app.route("/diagnostics")
def diagnostics():
    info = {}
    info["SECRET_KEY_set"] = bool(os.environ.get("SECRET_KEY"))
    info["DATABASE_URL_set"] = bool(os.environ.get("DATABASE_URL"))
    info["database_uri"] = app.config["SQLALCHEMY_DATABASE_URI"]

    # Try database connection
    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            result = conn.execute(text("SELECT NOW()")).scalar()
        info["database_connection"] = "OK"
        info["current_time_in_db"] = str(result)
    except Exception as e:
        info["database_connection"] = f"FAILED - {e}"

    return jsonify(info)

# ===================== RUN =====================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')
