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
elif [ "$1" = "cli" ]; then
    echo "Starting CLI system..."
    python main.py
else
    echo "Usage: $0 [streamlit|cli]"
    echo "  streamlit - Run Streamlit web interface"
    echo "  cli - Run command-line interface"
    exit 1
fi