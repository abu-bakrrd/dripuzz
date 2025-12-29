#!/bin/bash

echo "Starting E-Commerce application..."

# Seed database
echo "Seeding database..."
python seed_db.py

# Start Flask application
echo "Starting Flask server..."
python app.py
