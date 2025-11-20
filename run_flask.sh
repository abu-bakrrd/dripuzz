#!/bin/bash

# Run Flask app on port 5000 (pure Flask without Node.js)
echo "Starting Flask application on port 5000..."

# Seed database
echo "Seeding database..."
python seed_db.py

# Start Flask
echo "Starting Flask server..."
PORT=5000 python app.py
