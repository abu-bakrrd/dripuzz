cd "$(dirname "$0")/.."

# Seed database
echo "Seeding database..."
python scripts/seed_db.py

# Start Flask
echo "Starting Flask server..."
PORT=5000 python app.py
