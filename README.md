# AI Attendance System

A comprehensive AI-powered attendance system using computer vision for automatic student attendance tracking.

## Features

- **Real-time Face Detection**: YOLOv8 and OpenCV Haar Cascade support with automatic fallback
- **Face Recognition**: FaceNet and Dlib-based recognition with optimized caching and batch processing
- **Liveness Detection**: MediaPipe-based anti-spoofing to prevent photo/video attacks
- **5-minute Attendance Window**: Configurable attendance capture during class sessions
- **Uncertain Match Handling**: Flag low-confidence matches for admin review
- **Database Integration**: SQLAlchemy-based attendance record management
- **Admin Interface**: Enhanced Web dashboard with real-time monitoring
- **Configuration Management**: Centralized config with environment variable support
- **Performance Monitoring**: Real-time performance metrics and optimization
- **Security Features**: Input validation, secure file handling, and privacy protection
- **Comprehensive Testing**: Unit tests, integration tests, and performance benchmarks
- **Multi-threading**: Asynchronous processing for better performance

## System Architecture

```
ai-attendance-system/
├── src/
│   ├── face_detection/          # Face detection modules
│   │   ├── yolo_detector.py     # YOLOv8-face detector
│   │   └── haar_detector.py     # OpenCV Haar Cascade detector
│   ├── face_recognition/        # Face recognition modules
│   │   ├── facenet_recognizer.py # FaceNet-based recognition
│   │   ├── dlib_recognizer.py   # Dlib-based recognition
│   │   └── matcher.py          # Unified face matching
│   ├── liveness_detection/      # Anti-spoofing modules
│   │   └── mediapipe_liveness.py # MediaPipe liveness detection
│   ├── database/               # Database models and management
│   │   └── models.py          # SQLAlchemy models
│   ├── camera_pipeline/        # Camera processing pipeline
│   │   └── attendance_system.py # Main processing logic
│   ├── web/                    # Web application routes
│   │   ├── auth.py
│   │   ├── student.py
│   │   ├── teacher.py
│   │   ├── admin.py
│   │   └── ...
│   └── api/                    # API endpoints
├── models/                     # Pre-trained model files
├── data/                       # Data storage
│   ├── students/              # Student reference photos
│   ├── attendance/            # Attendance records
│   └── uncertain_matches/     # Uncertain matches for review
├── config/                     # Configuration files
├── tests/                      # Test files
├── requirements.txt            # Python dependencies
├── app.py                      # Web Application Entry Point
└── run_camera.py               # Camera Attendance Entry Point
```

## Installation

### Prerequisites

- Python 3.8+
- OpenCV 4.5+
- Camera (USB or IP)

### Setup

1. **Clone the repository**:
```bash
git clone <repository-url>
cd ai-attendance-system
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Download required models**:
   - YOLOv8-face model (optional, will fallback to Haar Cascade)
   - Dlib face landmarks model (optional)
   - MediaPipe models (auto-downloaded)

4. **Create data directories**:
```bash
mkdir -p data/{students,attendance,uncertain_matches}
mkdir -p models
```

## Usage

### Web Application

1. **Run the web server**:
```bash
python app.py
```
Access the dashboard at `http://localhost:5000`.

**Default Credentials**:
- Admin: `admin@school.edu` / `admin456`
- Teacher: `teacher@school.edu` / `teacher123`
- Student: `student@school.edu` / `student123`

### Camera Attendance

1. **Run the camera system**:
```bash
python run_camera.py
```
You will be prompted to enter the Class ID to start the session.

2. **Controls**:
   - `q` - Quit the system

### Advanced Usage

1. **Initialize student database**:
```python
from src.face_recognition.matcher import FaceMatcher

matcher = FaceMatcher()
# Add student faces
matcher.add_known_face(face_image, "STU001", "John Doe")
matcher.save_known_faces("data/face_database.pkl")
```

2. **Configure system**:
```python
from src.config import config

# Set configuration values
config.set('camera.resolution.width', 1920)
config.set('attendance.confidence_threshold', 0.8)

# Save configuration
config.save_config()
```

## Configuration

### Face Detection
- **Primary**: YOLOv8-face (if available)
- **Fallback**: OpenCV Haar Cascade
- **Confidence threshold**: 0.5 (configurable)

### Face Recognition
- **Primary**: FaceNet (if available)
- **Fallback**: Feature-based matching
- **Tolerance**: 0.6 (configurable)

### Liveness Detection
- **Primary**: MediaPipe face mesh analysis
- **Fallback**: Edge detection and texture analysis
- **Threshold**: 0.6 (configurable)

## Database Schema

The system uses SQLAlchemy with the following main tables:

- **students**: Student information and face encodings
- **classes**: Class/room information
- **attendance_sessions**: Attendance tracking sessions
- **attendance_records**: Individual attendance records
- **uncertain_matches**: Low-confidence matches for review
- **system_logs**: System logging and debugging

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation

---

**Note**: This system is designed for educational and research purposes. Ensure compliance with privacy laws and regulations when deploying in production environments.
