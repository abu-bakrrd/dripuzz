#!/usr/bin/env python3
"""
Initialize database tables (run this once before starting the app)
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

# Load environment variables from project root .env
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

from backend.database import init_db

if __name__ == '__main__':
    print("Creating database tables if they don't exist...")
    init_db()
    print("Database tables created successfully!")
    print("\nTo seed sample data, run: python seed_db.py")
