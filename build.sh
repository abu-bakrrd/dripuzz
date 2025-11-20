#!/bin/bash

set -e

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Installing Node.js dependencies..."
npm ci

echo "Building frontend..."
npm run build

echo "Build completed successfully!"
