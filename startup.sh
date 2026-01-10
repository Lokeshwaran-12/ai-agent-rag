#!/bin/bash
echo "--- STARTUP.SH EXECUTING ---"

# Install dependencies explicitly
echo "Installing dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Start the application
echo "Starting Uvicorn..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
