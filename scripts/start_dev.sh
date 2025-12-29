#!/bin/bash
# Start Flask API and Vite dev server for development

# Navigate to project root
cd "$(dirname "$0")/.."

# Start Flask API in background on port 5000
python app.py &
FLASK_PID=$!

# Start Vite dev server on port 5173 with proxy to Flask
npx vite --port 5173 --host 0.0.0.0 &
VITE_PID=$!

# Wait for both processes
wait $FLASK_PID $VITE_PID
