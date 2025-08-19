import requests
import uuid
import time
import threading
from datetime import datetime, timezone
import random

class MobileClient:
    def __init__(self, server_url):
        self.server_url = server_url
        self.device_serial = f"DEV-{uuid.uuid4().hex[:10].upper()}"
        self.running = False
        self.thread = None

    def get_current_location(self):
        """Simulate getting GPS coordinates"""
        latitude = -1.286389 + random.uniform(-0.001, 0.001)
        longitude = 36.817223 + random.uniform(-0.001, 0.001)
        return {
            "latitude": round(latitude, 6),
            "longitude": round(longitude, 6),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def register_device(self):
        """Register device with server"""
        device_data = {
            "serial_number": self.device_serial,
            "name": "Test Phone",
            "make": "Generic",
            "model": "Simulated GPS",
            "device_type": "Phone",
            "current_status": "Active",
            "current_location": "Initial Registration",
            "latitude": None,
            "longitude": None,
            "user_id": 1
        }

        print("Registering device...")
        try:
            response = requests.post(
                f"{self.server_url}/api/register_device",
                json=device_data,
                timeout=10
            )
            if response.status_code == 200:
                print(f"✅ Device registered: {self.device_serial}")
                return True
            else:
                print(f"❌ Registration failed: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print(f"❌ Error registering device: {e}")
            return False

    def report_location(self):
        """Send location update to tracking server"""
        try:
            location = self.get_current_location()
            update_data = {
                "serial_number": self.device_serial,
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "last_seen": datetime.now(timezone.utc).isoformat(),
                "current_location": f"Updated at {location['timestamp']}",
                "current_status": "Active"
            }

            response = requests.post(
                f"{self.server_url}/api/report_location",
                json=update_data,
                timeout=10
            )

            if response.status_code == 200:
                print(f"📍 Location updated: {location['latitude']}, {location['longitude']}")
            else:
                print(f"❌ Location update failed: {response.status_code}")
                print(response.text)

        except Exception as e:
            print(f"❌ Error reporting location: {e}")

    def start_reporting(self):
        """Start sending updates in a background thread"""
        if not self.running:
            if not self.register_device():
                print("❌ Could not start reporting (registration failed).")
                return
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            print("▶️ Started location reporting...")

    def stop_reporting(self):
        """Stop sending updates"""
        if self.running:
            self.running = False
            print("⏹️ Stopping location reporting...")
            if self.thread:
                self.thread.join()
                self.thread = None
            print("✅ Reporting stopped.")

    def _run_loop(self):
        """Loop that sends updates until stopped"""
        while self.running:
            self.report_location()
            time.sleep(5)

if __name__ == "__main__":
    client = MobileClient("http://127.0.0.1:5000")

    print("📱 Device Tracking Client v2.0")
    print("========================================")
    print(f"Device Serial: {client.device_serial}")

    while True:
        print("\nChoose an option:")
        print("1. Start sending updates")
        print("2. Stop sending updates")
        print("3. Exit")
        choice = input("> ")

        if choice == "1":
            client.start_reporting()
        elif choice == "2":
            client.stop_reporting()
        elif choice == "3":
            client.stop_reporting()
            print("👋 Exiting client...")
            break
        else:
            print("❌ Invalid choice, try again.")
