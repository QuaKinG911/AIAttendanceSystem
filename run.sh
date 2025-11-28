#!/bin/bash
# AI Attendance System Launcher

cd "$(dirname "$0")"

# Check for virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the system
echo "Starting Flask web application..."
python3 app.py