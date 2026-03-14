#!/bin/bash

# Navigate to the backend directory
cd "$(dirname "$0")/web/backend"

# Ensure venv is active (assume ../../venv is the root venv)
if [ -d "../../venv" ]; then
    source ../../venv/bin/activate
fi

echo "🚀 Starting AI Book Factory Premium Dashboard..."
echo "🔗 Access at: http://localhost:8000"

# Run Uvicorn - app is in app/main.py, object is app
# We use --reload for development
export PYTHONPATH=$PYTHONPATH:$(pwd)
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
