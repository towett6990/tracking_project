#!/usr/bin/env python3
"""
Database initialization script for production deployment
"""
from tracking_software import app, db
import os

def init_database():
    """Initialize the database with tables"""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"📋 Created tables: {tables}")

if __name__ == "__main__":
    init_database()
