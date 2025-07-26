import sqlite3

# Connect to your existing database
conn = sqlite3.connect('devices.db')
cursor = conn.cursor()

# Add columns (will fail if already exist, so you can wrap in try/except)
try:
    cursor.execute("ALTER TABLE device ADD COLUMN latitude REAL")
    cursor.execute("ALTER TABLE device ADD COLUMN longitude REAL")
    print("✔️ Columns added successfully.")
except sqlite3.OperationalError as e:
    print("⚠️ Could not add columns:", e)

conn.commit()
conn.close()