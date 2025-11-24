# 🎓 AI Attendance System - Complete Guide

## 📋 **Table of Contents**
1. [How It Works](#how-it-works)
2. [Installation & Setup](#installation--setup)
3. [Creating Your Dataset](#creating-your-dataset)
4. [Running the System](#running-the-system)
5. [Configuration](#configuration)
6. [Troubleshooting](#troubleshooting)

---

## 🔍 **How It Works**

### **System Architecture**
```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Camera    │───▶│ Face        │───▶│ Liveness   │───▶│ Face         │───▶│ Attendance  │
│   Feed      │    │ Detection   │    │ Detection  │    │ Recognition  │    │ Database    │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘    └─────────────┘
```

### **Detailed Workflow**

#### **1. Camera Input**
- **Source**: USB camera, IP camera, or video file
- **Resolution**: 1280x720 (configurable)
- **Frame Rate**: 30 FPS (configurable)
- **Processing**: Real-time frame capture

#### **2. Face Detection**
- **Primary Model**: YOLOv8-face (if available)
  - High accuracy for crowded classrooms
  - Bounding box: `(x1, y1, x2, y2, confidence)`
- **Fallback**: OpenCV Haar Cascade
  - Always available, lightweight
  - Good for basic detection

#### **3. Liveness Detection**
- **Purpose**: Prevent photo/video spoofing
- **Primary**: MediaPipe Face Mesh
  - 468 facial landmarks
  - Eye blink detection
  - Head movement analysis
- **Fallback**: Basic CV techniques
  - Edge density analysis
  - Texture variance
  - Color variation

#### **4. Face Recognition**
- **Primary**: FaceNet (128D embeddings)
  - Deep learning features
  - High accuracy (>95%)
- **Fallback**: Feature-based matching
  - Histogram features
  - Cosine similarity

#### **5. Attendance Logic**
- **Time Window**: First 5 minutes of class
- **Duplicate Prevention**: One record per student
- **Confidence Threshold**: 70% for automatic marking
- **Uncertain Matches**: <70% flagged for admin review

---

## 🛠️ **Installation & Setup**

### **Option 1: Automated Setup**
```bash
# Clone or navigate to project
cd ai-attendance-system

# Run setup script
./setup.sh

# This will:
# - Install dependencies
# - Download models
# - Create directories
# - Generate config files
```

### **Option 2: Manual Setup**
```bash
# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p data/{students,attendance,uncertain_matches}
mkdir -p models logs
```

### **System Requirements**
- **Python**: 3.8+
- **RAM**: 4GB+ (8GB recommended)
- **Camera**: USB or IP camera
- **OS**: Linux, Windows, macOS

---

## 👥 **Creating Your Dataset**

### **Method 1: Interactive Registration (Recommended)**
```bash
python3 create_dataset.py
# Choose option 1
# Follow prompts to register each student
```

### **Method 2: Batch Import from Photos**
```bash
# Organize photos with naming: StudentID_Name.jpg
# Example: STU001_John_Doe.jpg
python3 create_dataset.py
# Choose option 2
# Provide directory path
```

### **Photo Requirements**
- **Format**: JPG, JPEG, PNG
- **Size**: Minimum 200x200 pixels
- **Quality**: Clear, well-lit, front-facing
- **Background**: Plain preferred
- **Naming**: `StudentID_Name.jpg`

### **Dataset Structure**
```
data/
├── students/
│   ├── STU001_John_Doe.jpg
│   ├── STU002_Jane_Smith.jpg
│   └── metadata.json
├── attendance/
└── uncertain_matches/
```

---

## 🚀 **Running the System**

### **1. Web Application**
Start the web dashboard for admin, teachers, and students:
```bash
python3 app.py
```
Access at `http://localhost:5000`.

### **2. Camera Attendance**
Start the camera system to record attendance:
```bash
python3 run_camera.py
```

### **Session Workflow**
1. **Start**: System initializes camera
2. **5-Minute Window**: Attendance capture begins
3. **Face Processing**: Real-time detection & recognition
4. **Automatic Marking**: High-confidence matches recorded
5. **Admin Review**: Uncertain matches flagged
6. **Report Generation**: JSON attendance reports

---

## ⚙️ **Configuration**

### **Main Config File** (`config/config.json`)
```json
{
    "camera": {
        "source": 0,
        "resolution": {"width": 1280, "height": 720},
        "fps": 30
    },
    "attendance": {
        "duration_minutes": 5,
        "confidence_threshold": 0.7,
        "liveness_threshold": 0.6
    },
    "detection": {
        "model": "yolo",
        "confidence_threshold": 0.5,
        "fallback_to_haar": true
    },
    "recognition": {
        "model": "facenet",
        "tolerance": 0.6,
        "database_path": "data/face_database.pkl"
    }
}
```

### **Key Settings**
- **attendance.duration_minutes**: Time window for attendance
- **attendance.confidence_threshold**: Minimum confidence for auto-marking
- **detection.model**: "yolo" or "haar"
- **recognition.tolerance**: Face matching sensitivity (0.4-0.8)

---

## 🐛 **Troubleshooting**

### **Common Issues**

#### **Camera Not Detected**
```bash
# Check available cameras
python3 -c "import cv2; print([i for i in range(10) if cv2.VideoCapture(i).read()[0]])"

# Try different camera indices
# Update config.json or environment variable ATTENDANCE_CAMERA_SOURCE
```

#### **Face Detection Not Working**
```bash
# Check Haar cascade file
ls -la haarcascade_frontalface_default.xml

# Download if missing
wget -O haarcascade_frontalface_default.xml \
  https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml
```

#### **Recognition Accuracy Low**
- Improve lighting conditions
- Ensure high-quality reference photos
- Adjust confidence threshold in config
- Add multiple reference photos per student

#### **Performance Issues**
- Reduce camera resolution
- Lower FPS settings
- Use GPU if available
- Close unnecessary applications

### **Debug Mode**
```bash
# Enable debug logging
export ATTENDANCE_LOG_LEVEL=DEBUG
python3 app.py
```

---

## 📊 **Expected Performance**

### **Accuracy Metrics**
- **Face Detection**: >95% accuracy
- **Face Recognition**: >90% accuracy
- **Liveness Detection**: >85% accuracy
- **Overall System**: >80% accuracy

### **Performance Metrics**
- **Processing Speed**: 15-30 FPS
- **Memory Usage**: 2-4GB
- **CPU Usage**: 30-50% (varies by model)
- **Startup Time**: <10 seconds

---

## 📞 **Support**

### **Getting Help**
1. Check this guide first
2. Review log files in `logs/` directory
3. Test individual components
4. Check system requirements
5. Create issue with detailed error info

### **Log Files**
- Main log: `logs/attendance_system.log`
- Error log: `logs/errors.log`
- Performance log: `logs/performance.log`

---

This comprehensive guide should help you understand, install, configure, and run the AI Attendance System effectively! 🎓