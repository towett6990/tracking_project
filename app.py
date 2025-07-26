from flask import Flask, request, jsonify, render_template
from datetime import datetime

app = Flask(__name__)

# In-memory store for demo purposes
devices = {}

@app.route('/')
def index():
    return render_template('index.html', devices=devices)

@app.route('/add_device', methods=['POST'])
def add_device():
    data = request.form
    serial = data.get('serial')
    devices[serial] = {
        "make": data.get('make'),
        "model": data.get('model'),
        "location": None,
        "last_updated": None
    }
    return "Device added successfully. <a href='/'>Go back</a>"

@app.route('/search')
def search():
    serial = request.args.get('serial')
    device = devices.get(serial)
    return render_template('search.html', device=device, serial=serial)

@app.route('/track')
def track_page():
    return render_template('tracker.html')

@app.route('/api/report_location', methods=['POST'])
def report_location():
    data = request.json
    serial = data.get('serial')
    lat = data.get('latitude')
    lon = data.get('longitude')
    if serial in devices:
        devices[serial]["location"] = {"lat": lat, "lon": lon}
        devices[serial]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Device not found"}), 404

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
