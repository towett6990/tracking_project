import requests
import time
import random

SERVER_URL = "http://127.0.0.1:5000/api/report_location"
SERIAL_NUMBER = "5CG63351S8"

# Starting location (e.g., Nairobi)
latitude = -1.2833
longitude = 36.8167

while True:
    # Slightly change location
    latitude += random.uniform(-0.0005, 0.0005)
    longitude += random.uniform(-0.0005, 0.0005)

    payload = {
        "serial_number": SERIAL_NUMBER,
        "latitude": latitude,
        "longitude": longitude
    }

    try:
        response = requests.post(SERVER_URL, json=payload)
        print(f"[{time.strftime('%H:%M:%S')}] Sent: {payload} | Response: {response.status_code}")
    except Exception as e:
        print(f"Error sending location: {e}")

    time.sleep(5)  # Wait 5 seconds before sending next update
