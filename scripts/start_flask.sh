#!/bin/bash
# Initialize database and start Flask server
cd "$(dirname "$0")/.."
python scripts/seed_db.py
python app.py
