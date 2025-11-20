#!/bin/bash
# Production start script for Render
# Database tables are created automatically on startup by app.py
# To seed sample data, run: python seed_db.py (manually, one time only)

echo "Starting production server with Gunicorn..."
gunicorn app:app --bind 0.0.0.0:$PORT --workers 4 --timeout 120
