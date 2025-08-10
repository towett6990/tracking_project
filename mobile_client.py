#!/usr/bin/env python3
"""
Mobile Client Component for Device Tracking System
This component would be installed on mobile devices to enable tracking
"""

import json
import time
import threading
import requests
from datetime import datetime
import hashlib
import uuid

class DeviceTracker:
    def __init__(self, server_url="http://127.0.0.1:5000", device_serial=None):
        self.server_url = server_url
        self.device_serial = device_serial or self.generate_device_serial()
        self.is_running = False
        self.tracking_thread = None
        self.last_location = None
        self.device_info = self.get_device_info()
        
    def generate_device_serial(self):
        """Generate unique device serial number"""
        # In real implementation, this would be hardware-based
        mac_address = uuid.getnode()
        device_id = hashlib.md5(str(mac_address).encode()).hexdigest()[:12].upper()
        return f"DEV-{device_id}"
    
    def get_device_info(self):
        """Get device information"""
        # In real implementation, this would query actual device specs
        return {
            "serial_number": self.device_serial,
            "make": "TestPhone",
            "model": "TrackPro X1",
            "device_type": "Smartphone",
            "os_version": "Android 14",
            "app_version": "1.0.0"
        }
    
    def get_current_location(self):
        """Simulate getting current GPS location"""
        # In real implementation, this would use actual GPS/network location
        import random
        
        # Simulate GPS coordinates with slight movement
        if self.last_location:
            lat = self.last_location['latitude'] + random.uniform(-0.0001, 0.0001)
            lon = self.last_location['longitude'] + random.uniform(-0.0001, 0.0001)
        else:
            # Default to New York area for demo
            lat = 40.7128 + random.uniform(-0.01, 0.01)
            lon = -74.0060 + random.uniform(-0.01, 0.01)
        
        location = {
            "latitude": lat,
            "longitude": lon,
            "accuracy": random.uniform(5, 50),  # meters
            "timestamp": datetime.utcnow().isoformat(),
            "method": "GPS"  # GPS, Network, Passive
        }
        
        self.last_location = location
        return location
    
    def register_device(self):
        """Register device with tracking server"""
        try:
            location = self.get_current_location()
            
            registration_data = {
                "serial_number": self.device_serial,
                "make": self.device_info["make"],
                "model": self.device_info["model"],
                "device_type": self.device_info["device_type"],
                "current_status": "Active",
                "current_location": f"Auto-registered at {location['timestamp']}",
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "device_info": self.device_info
            }
            
            response = requests.post(
                f"{self.server_url}/api/register_device",
                json=registration_data,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Device registered: {self.device_serial}")
                return True
            else:
                print(f"❌ Registration failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False
    
    def report_location(self):
        """Report current location to server"""
        try:
            location = self.get_current_location()
            
            report_data = {
                "serial_number": self.device_serial,
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "accuracy": location["accuracy"],
                "method": location["method"],
                "battery_level": self.get_battery_level(),
                "network_type": self.get_network_type()
            }
            
            response = requests.post(
                f"{self.server_url}/api/report_location",
                json=report_data,
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"📍 Location reported: ({location['latitude']:.6f}, {location['longitude']:.6f})")
                return True
            else:
                print(f"❌ Location report failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Location report error: {e}")
            return False
    
    def get_battery_level(self):
        """Simulate battery level"""
        import random
        return random.randint(20, 100)
    
    def get_network_type(self):
        """Simulate network type"""
        import random
        return random.choice(["WiFi", "4G", "5G", "3G"])
    
    def check_for_commands(self):
        """Check for remote commands from server"""
        try:
            response = requests.get(
                f"{self.server_url}/api/device_commands/{self.device_serial}",
                timeout=5
            )
            
            if response.status_code == 200:
                commands = response.json()
                for command in commands:
                    self.execute_command(command)
                return True
            return False
            
        except Exception as e:
            print(f"❌ Command check error: {e}")
            return False
    
    def execute_command(self, command):
        """Execute remote command"""
        cmd_type = command.get("type")
        
        if cmd_type == "ping":
            print("📡 Received PING command - responding...")
            self.report_location()
        
        elif cmd_type == "locate":
            print("🎯 Received LOCATE command - sending precise location...")
            # Send high-accuracy location
            self.report_location()
        
        elif cmd_type == "alert":
            print("🚨 Received ALERT command - device would beep/vibrate...")
            # In real implementation: trigger sound/vibration
        
        elif cmd_type == "lock":
            print("🔒 Received LOCK command - device would be locked...")
            # In real implementation: lock device
        
        elif cmd_type == "wipe":
            print("💥 Received WIPE command - device would be wiped...")
            # In real implementation: secure wipe (with proper safeguards)
        
        # Acknowledge command execution
        try:
            requests.post(
                f"{self.server_url}/api/command_ack",
                json={
                    "serial_number": self.device_serial,
                    "command_id": command.get("id"),
                    "status": "executed",
                    "timestamp": datetime.utcnow().isoformat()
                },
                timeout=5
            )
        except:
            pass
    
    def tracking_loop(self):
        """Main tracking loop"""
        print(f"🔄 Starting tracking for device: {self.device_serial}")
        
        while self.is_running:
            try:
                # Report location every 30 seconds
                self.report_location()
                
                # Check for commands every 10 seconds
                self.check_for_commands()
                
                # Sleep for 10 seconds
                time.sleep(10)
                
            except KeyboardInterrupt:
                print("🛑 Tracking stopped by user")
                break
            except Exception as e:
                print(f"❌ Tracking error: {e}")
                time.sleep(30)  # Wait longer on error
    
    def start_tracking(self):
        """Start background tracking"""
        if not self.is_running:
            self.is_running = True
            self.tracking_thread = threading.Thread(target=self.tracking_loop)
            self.tracking_thread.daemon = True
            self.tracking_thread.start()
            print("✅ Tracking started")
    
    def stop_tracking(self):
        """Stop background tracking"""
        self.is_running = False
        if self.tracking_thread:
            self.tracking_thread.join(timeout=5)
        print("🛑 Tracking stopped")
    
    def emergency_mode(self):
        """Emergency tracking mode - more frequent updates"""
        print("🚨 EMERGENCY MODE ACTIVATED")
        
        while True:
            try:
                self.report_location()
                self.check_for_commands()
                time.sleep(5)  # Report every 5 seconds in emergency
            except KeyboardInterrupt:
                break

# Demo usage
if __name__ == "__main__":
    print("📱 Device Tracking Client v1.0")
    print("=" * 40)
    
    # Initialize tracker
    tracker = DeviceTracker()
    
    print(f"Device Serial: {tracker.device_serial}")
    print("Registering device...")
    
    # Register device
    if tracker.register_device():
        print("Starting tracking...")
        tracker.start_tracking()
        
        try:
            # Keep running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            tracker.stop_tracking()
            print("👋 Goodbye!")
    else:
        print("❌ Failed to register device")
