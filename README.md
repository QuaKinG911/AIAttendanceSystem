# AI Attendance System

A comprehensive AI-powered attendance system using computer vision for automatic student attendance tracking.

## Features

- **Real-time Face Detection**: YOLOv8 and OpenCV Haar Cascade support with automatic fallback
- **Face Recognition**: FaceNet and Dlib-based recognition with optimized caching and batch processing
- **Liveness Detection**: MediaPipe-based anti-spoofing to prevent photo/video attacks
- **5-minute Attendance Window**: Configurable attendance capture during class sessions
- **Uncertain Match Handling**: Flag low-confidence matches for admin review
- **Database Integration**: SQLAlchemy-based attendance record management
- **Admin Interface**: Enhanced Streamlit web dashboard with real-time monitoring
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
│   └── admin_interface/        # Web admin interface
├── models/                     # Pre-trained model files
├── data/                       # Data storage
│   ├── students/              # Student reference photos
│   ├── attendance/            # Attendance records
│   └── uncertain_matches/     # Uncertain matches for review
├── config/                     # Configuration files
├── tests/                      # Test files
├── requirements.txt            # Python dependencies
└── main.py                    # Main entry point
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

### Basic Usage

1. **Run the simple attendance system**:
```bash
python main.py
```

2. **Controls**:
   - `q` - Quit the system
   - `s` - Save attendance records
   - `r` - Reset attendance session

### Advanced Usage

1. **Initialize student database**:
```python
from src.face_recognition.matcher import FaceMatcher

matcher = FaceMatcher()
# Add student faces
matcher.add_known_face(face_image, "STU001", "John Doe")
matcher.save_known_faces("data/face_database.pkl")
```

2. **Run with specific camera**:
```python
from main import SimpleAttendanceSystem

system = SimpleAttendanceSystem(camera_source="rtsp://camera-url")
system.run()
```

3. **Run tests**:
```bash
python run_tests.py
```

4. **Configure system**:
```python
from src.config import config

# Set configuration values
config.set('camera.resolution.width', 1920)
config.set('attendance.confidence_threshold', 0.8)

# Save configuration
config.save_config()
```

5. **Monitor performance**:
```python
from src.performance import performance_monitor

# Get current stats
stats = performance_monitor.get_stats()
print(f"FPS: {stats['fps']:.2f}")
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

## API Reference

### Face Detection

```python
from src.face_detection.yolo_detector import YOLOFaceDetector

detector = YOLOFaceDetector()
faces = detector.detect_faces_with_confidence(image)
# Returns: [(x1, y1, x2, y2, confidence), ...]
```

### Face Recognition

```python
from src.face_recognition.matcher import FaceMatcher

matcher = FaceMatcher()
matcher.load_known_faces("database.pkl")
student_id, name, confidence = matcher.recognize_face(face_encoding)
```

### Liveness Detection

```python
from src.liveness_detection.mediapipe_liveness import MediaPipeLivenessDetector

detector = MediaPipeLivenessDetector()
result = detector.detect_liveness(image, face_bbox)
# Returns: {'is_live': bool, 'liveness_score': float, 'analysis': dict}
```

## Performance

- **Processing Speed**: 15-30 FPS on modern hardware (configurable)
- **Accuracy**: >95% face recognition accuracy with confidence thresholding
- **Liveness Detection**: >85% spoof detection rate with multiple methods
- **Memory Usage**: 2-4GB RAM with all models loaded (optimized resource management)
- **CPU Usage**: 30-50% during active processing (multi-threaded optimization)

## Recent Improvements

### v2.0 Enhancements
- **Configuration System**: Centralized configuration with JSON files and environment variables
- **Enhanced UI**: Improved Streamlit interface with real-time updates and better layout
- **Performance Optimization**: Multi-threading, caching, and resource management
- **Security Features**: Input validation, secure file handling, and privacy protection
- **Comprehensive Testing**: Unit tests, integration tests, and performance benchmarks
- **Error Handling**: Graceful fallbacks and detailed error reporting
- **Monitoring**: Real-time performance metrics and system health monitoring

## Troubleshooting

### Common Issues

1. **Camera not detected**:
   - Check camera connection
   - Verify camera permissions
   - Try different camera index

2. **Face recognition not working**:
   - Ensure proper lighting
   - Check face database exists
   - Verify face image quality

3. **Liveness detection failing**:
   - Ensure proper face orientation
   - Check for sufficient lighting
   - Verify MediaPipe installation

### Model Dependencies

The system is designed to work with fallback options:
- If YOLOv8 is not available → Uses Haar Cascade
- If FaceNet is not available → Uses feature matching
- If MediaPipe is not available → Uses basic CV techniques

### Configuration

The system uses a centralized configuration system. Configuration can be set via:

1. **JSON Configuration File** (`config/settings.json`):
```json
{
  "camera": {
    "source": 0,
    "resolution": {"width": 1280, "height": 720}
  },
  "attendance": {
    "duration_minutes": 5,
    "confidence_threshold": 0.7
  }
}
```

2. **Environment Variables**:
```bash
export ATTENDANCE_CAMERA_SOURCE=1
export ATTENDANCE_CONFIDENCE_THRESHOLD=0.8
```

### Testing

Run the comprehensive test suite:
```bash
python run_tests.py
```

This will run:
- Unit tests for individual components
- Integration tests for system workflows
- Performance benchmarks
- Existing validation scripts

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation

---

**Note**: This system is designed for educational and research purposes. Ensure compliance with privacy laws and regulations when deploying in production environments.
