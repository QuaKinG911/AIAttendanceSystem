#!/bin/bash

# AI Attendance System Setup Script

echo "🎓 AI Attendance System Setup"
echo "=============================="

# Check Python version
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
if [[ $(echo "$python_version >= 3.8" | bc -l) -eq 0 ]]; then
    echo "❌ Python 3.8+ is required. Current version: $python_version"
    exit 1
fi

echo "✓ Python version: $python_version"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install system dependencies
echo "Installing system dependencies..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y python3-dev cmake libopenblas-dev liblapack-dev \
        libx11-dev libgtk-3-dev python3-tk
elif command -v yum &> /dev/null; then
    sudo yum install -y python3-devel cmake libopenblas-devel liblapack-devel \
        libX11-devel gtk3-devel python3-tkinter
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p data/{students,attendance,uncertain_matches}
mkdir -p models
mkdir -p logs

# Download YOLOv8 face model if not present
echo "Downloading YOLOv8 face model..."
if [ ! -f "models/yolov8x-face-lindevs.pt" ]; then
    wget -O models/yolov8x-face-lindevs.pt \
        https://github.com/lindevs/yolov8-face/releases/download/v0.0.0/yolov8x-face-lindevs.pt
fi

# Create config file
echo "Creating configuration file..."
cat > config/config.json << EOF
{
    "camera": {
        "source": 0,
        "resolution": {
            "width": 1280,
            "height": 720
        },
        "fps": 30
    },
    "attendance": {
        "duration_minutes": 5,
        "confidence_threshold": 0.7,
        "liveness_threshold": 0.6
    },
    "detection": {
        "model": "yolo",
        "confidence_threshold": 0.5
    },
    "recognition": {
        "model": "facenet",
        "tolerance": 0.6,
        "database_path": "data/face_database.pkl"
    },
    "liveness": {
        "enabled": true,
        "method": "mediapipe",
        "threshold": 0.6
    },
    "database": {
        "url": "sqlite:///data/attendance.db"
    },
    "logging": {
        "level": "INFO",
        "file": "logs/attendance_system.log"
    }
}
EOF

# Create startup script
echo "Creating startup script..."
cat > start.sh << 'EOF'
#!/bin/bash

# AI Attendance System Startup Script

cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Run the system
python app.py
EOF

chmod +x start.sh

# Create student registration script
echo "Creating student registration script..."
cat > register_student.py << 'EOF'
#!/usr/bin/env python3

import cv2
import os
import sys
import pickle
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from face_recognition.matcher import FaceMatcher
except ImportError:
    print("❌ Face recognition module not available")
    sys.exit(1)

def register_student():
    """Register a new student"""
    print("🎓 Student Registration")
    print("=======================")
    
    # Get student information
    student_id = input("Enter Student ID: ").strip()
    name = input("Enter Student Name: ").strip()
    email = input("Enter Email (optional): ").strip()
    
    if not student_id or not name:
        print("❌ Student ID and Name are required")
        return
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Failed to open camera")
        return
    
    print("\n📷 Position your face in the camera frame")
    print("Press 'c' to capture, 'q' to quit")
    
    face_matcher = FaceMatcher()
    
    # Load existing database
    db_path = "data/face_database.pkl"
    if os.path.exists(db_path):
        face_matcher.load_known_faces(db_path)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Display frame
        cv2.imshow('Student Registration', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('c'):
            # Capture face
            success = face_matcher.add_known_face(frame, student_id, name)
            if success:
                print(f"✓ Student {name} registered successfully")
                
                # Save database
                face_matcher.save_known_faces(db_path)
                
                # Save face image
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"data/students/{student_id}_{name.replace(' ', '_')}_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                print(f"✓ Face image saved: {filename}")
                
                break
            else:
                print("❌ Failed to register face. Please try again.")
        
        elif key == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    register_student()
EOF

chmod +x register_student.py

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Register students: python register_student.py"
echo "3. Run the system: ./start.sh"
echo ""
echo "Configuration file: config/config.json"
echo "Logs will be saved to: logs/attendance_system.log"