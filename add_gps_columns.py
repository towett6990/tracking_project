import sqlite3

conn = sqlite3.connect('devices.db')  # ✅ Use same database name
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE devices ADD COLUMN latitude TEXT")
    print("✅ Added latitude column.")
except sqlite3.OperationalError as e:
    print(f"⚠ {e}")

try:
    cursor.execute("ALTER TABLE devices ADD COLUMN longitude TEXT")
    print("✅ Added longitude column.")
except sqlite3.OperationalError as e:
    print(f"⚠ {e}")

conn.commit()
conn.close()
