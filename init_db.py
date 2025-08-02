#!/usr/bin/env python3
"""
Database initialization script for production deployment
"""
from tracking_software import app, db
import os

def init_database():
    """Initialize the database with tables"""
    with app.app_context():
        # Drop all tables first to ensure clean schema
        print("🗑️ Dropping existing tables...")
        db.drop_all()
        
        # Create all tables with correct schema
        print("🔨 Creating tables with updated schema...")
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"📋 Created tables: {tables}")
        
        # Show columns for user table
        if 'user' in tables:
            columns = inspector.get_columns('user')
            column_names = [col['name'] for col in columns]
            print(f"👤 User table columns: {column_names}")

if __name__ == "__main__":
    init_database()
