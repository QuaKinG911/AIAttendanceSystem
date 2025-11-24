#!/bin/bash
# AI Attendance System Launcher
# This script activates the virtual environment and runs the system

cd "$(dirname "$0")"

# Activate virtual environment
source .venv311/bin/activate

# Run the system
if [ "$1" = "streamlit" ]; then
    echo "Starting Streamlit UI..."
    streamlit run ui/streamlit_app.py
elif [ "$1" = "web" ]; then
    echo "Starting Flask web application..."
    python app.py
else
    echo "Usage: $0 [streamlit|web]"
    echo "  streamlit - Run Streamlit web interface"
    echo "  web - Run Flask web application"
    exit 1
fi