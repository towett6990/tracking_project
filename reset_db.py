#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from tracking_software import app, db

def reset_database():
    with app.app_context():
        print('Dropping all tables...')
        db.drop_all()
        print('Creating all tables with correct schema...')
        db.create_all()
        print('Database reset complete!')
        
        # Verify the new schema
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f'Tables created: {tables}')
        
        if 'user' in tables:
            user_columns = inspector.get_columns('user')
            print('New user table columns:')
            for col in user_columns:
                print(f'  - {col["name"]}: {col["type"]}')

if __name__ == '__main__':
    reset_database()
