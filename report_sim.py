import requests

# Step 1: Get IP-based location
def get_location_by_ip():
    try:
        res = requests.get('https://ipinfo.io/json')
        data = res.json()
        loc = data['loc'].split(',')
        return float(loc[0]), float(loc[1])
    except Exception as e:
        print("Failed to get location:", e)
        return None, None

# Step 2: Prompt for serial number
serial = input("Enter your device serial number: ").strip()
lat, lon = get_location_by_ip()

if lat is None or lon is None:
    print("Could not determine your location.")
else:
    # Step 3: Send location to Flask app
    res = requests.post("http://127.0.0.1:5000/api/report_location", json={
        "serial_number": serial,
        "latitude": lat,
        "longitude": lon
    })

    if res.status_code == 200:
        print("📍 Device location updated:", res.json().get("location"))
    else:
        print("❌ Error:", res.json())
