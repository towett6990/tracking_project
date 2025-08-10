import requests
import subprocess
import platform
import time
import geocoder  # Make sure to install this with: pip install geocoder
import logging
from datetime import datetime

# ========== CONFIG ==========
SERVER_URL = "http://localhost:5000/api/report_location"  # Change if using public server
PING_INTERVAL = 60  # seconds

# ========== SETUP LOGGING ==========
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

# ========== GET SERIAL NUMBER ==========
def get_serial_number():
    try:
        system = platform.system()
        if system == "Windows":
            result = subprocess.check_output("wmic bios get serialnumber", shell=True)
            serial = result.decode().split("\n")[1].strip()
        elif system == "Linux":
            result = subprocess.check_output("cat /sys/class/dmi/id/product_serial", shell=True)
            serial = result.decode().strip()
        elif system == "Darwin":
            result = subprocess.check_output("system_profiler SPHardwareDataType", shell=True)
            lines = result.decode().split("\n")
            serial = next((line.split(":")[1].strip() for line in lines if "Serial Number" in line), "UNKNOWN")
        else:
            serial = "UNKNOWN"
        return serial if serial else "UNKNOWN"
    except Exception as e:
        logging.warning(f"Failed to get serial number: {e}")
        return "UNKNOWN"

# ========== GET LOCATION USING IP ==========
def get_ip_location():
    try:
        g = geocoder.ip('me')
        if g.ok:
            return g.latlng  # [latitude, longitude]
    except Exception as e:
        logging.warning(f"Failed to get IP location: {e}")
    return None, None

# ========== MAIN LOOP ==========
def main():
    serial_number = get_serial_number()
    logging.info(f"🛰️ Starting tracker for device serial: {serial_number}")

    while True:
        latitude, longitude = get_ip_location()
        if latitude is None or longitude is None:
            logging.error("Could not retrieve IP-based location.")
        else:
            payload = {
                "serial_number": serial_number,
                "latitude": latitude,
                "longitude": longitude
            }
            logging.info(f"→ Sending: {payload}")
            try:
                response = requests.post(SERVER_URL, json=payload, timeout=10)
                if response.status_code == 200:
                    logging.info("✓ Location updated.")
                else:
                    logging.warning(f"Server responded with {response.status_code}: {response.text}")
            except requests.exceptions.RequestException as err:
                logging.error(f"Network error: {err}")

        time.sleep(PING_INTERVAL)

if __name__ == "__main__":
    main()
