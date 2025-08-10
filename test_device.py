#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from tracking_software import app, db, Device, User
from werkzeug.security import generate_password_hash

def test_device_creation():
    with app.app_context():
        print("=== DEVICE SEARCH TEST ===")
        
        # Check users
        users = User.query.all()
        print(f"Users in database: {len(users)}")
        
        if len(users) == 0:
            print("Creating test user...")
            user = User(
                username='testuser',
                email='test@example.com',
                password=generate_password_hash('password123')
            )
            db.session.add(user)
            db.session.commit()
            print("User created")
        else:
            user = users[0]
            print(f"Using existing user: {user.username}")
        
        # Create the device
        print(f"Creating device 10HE3D0ECC0003Z for user ID: {user.id}")
        
        # Delete existing device if any
        existing = Device.query.filter_by(serial_number='10HE3D0ECC0003Z').first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
            print("Deleted existing device")
        
        # Create new device
        device = Device(
            serial_number='10HE3D0ECC0003Z',
            make='Apple',
            model='iPhone 13',
            device_type='Smartphone',
            current_status='Active',
            current_location='New York, NY',
            latitude=40.7128,
            longitude=-74.0060,
            user_id=user.id
        )
        
        db.session.add(device)
        db.session.commit()
        print("Device added and committed")
        
        # Verify
        found_device = Device.query.filter_by(serial_number='10HE3D0ECC0003Z').first()
        if found_device:
            print("✅ SUCCESS! Device found:")
            print(f"  Serial: {found_device.serial_number}")
            print(f"  Make/Model: {found_device.make} {found_device.model}")
            print(f"  Location: {found_device.current_location}")
            print(f"  Coordinates: ({found_device.latitude}, {found_device.longitude})")
            return True
        else:
            print("❌ FAILED! Device not found after creation")
            return False

if __name__ == '__main__':
    result = test_device_creation()
    print(f"\nTest result: {'PASSED' if result else 'FAILED'}")
