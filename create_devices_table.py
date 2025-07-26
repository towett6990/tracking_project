# create_devices_table.py
import sqlite3

conn = sqlite3.connect('devices.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    serial_number TEXT NOT NULL,
    make TEXT,
    model TEXT,
    type TEXT,
    status TEXT,
    location TEXT
)
''')

conn.commit()
conn.close()
print("✅ devices table created.")
