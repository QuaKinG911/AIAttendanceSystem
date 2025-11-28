# 🎓 AI Attendance System

A comprehensive AI-powered attendance tracking system using computer vision for automatic student attendance monitoring in educational environments.

## ✨ Features

- **Real-time Face Detection**: YOLOv8 and OpenCV Haar Cascade with automatic fallback
- **Advanced Face Recognition**: FaceNet embeddings with cosine similarity matching
- **Liveness Detection**: MediaPipe-based anti-spoofing to prevent photo/video attacks
- **Multi-role User System**: Admin, Teacher, Student, and Parent dashboards
- **Flexible Attendance Logic**: Configurable time windows and confidence thresholds
- **Database Integration**: SQLAlchemy ORM with SQLite/PostgreSQL support
- **Web Interface**: Flask-based responsive dashboards with role-based access
- **REST API**: Complete API for integration with other systems
- **Real-time Processing**: Camera pipeline with multi-threading support
- **Analytics & Reporting**: ML-powered insights and performance monitoring
- **Security Features**: JWT authentication, input validation, and secure file handling

## 🏗️ System Architecture

```
ai-attendance-system/
├── src/
│   ├── api/                    # REST API endpoints
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── users.py           # User management
│   │   ├── attendance.py      # Attendance operations
│   │   ├── analytics.py       # Analytics and reporting
│   │   └── admin.py           # Administrative functions
│   ├── camera_pipeline/       # Real-time camera processing
│   │   └── attendance_system.py # Main attendance logic
│   ├── face_detection/        # Face detection modules
│   │   └── yolo_detector.py   # YOLOv8 face detector
│   ├── face_recognition/      # Face recognition system
│   │   └── matcher.py         # Face matching with embeddings
│   ├── liveness_detection/    # Anti-spoofing detection
│   │   └── mediapipe_liveness.py # MediaPipe liveness checks
│   ├── models.py              # Database models (SQLAlchemy)
│   ├── config.py              # Configuration management
│   └── web/                   # Web interface blueprints
│       ├── auth.py            # Login/logout
│       ├── admin.py           # Admin dashboard
│       ├── teacher.py         # Teacher interface
│       ├── student.py         # Student dashboard
│       └── parent.py          # Parent access
├── data/
│   ├── faces/                 # Student face images by ID
│   ├── attendance/            # Attendance records (JSON)
│   └── students/              # Student metadata
├── templates/                 # Jinja2 HTML templates
├── static/                    # CSS, JS, images
├── scripts/                   # Utility scripts
│   ├── build_face_database.py # Build recognition database
│   └── setup_models.py       # Model setup utilities
├── alembic/                   # Database migrations
├── config/                    # Configuration files
└── requirements.txt           # Python dependencies
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Camera (USB/IP webcam)
- 4GB+ RAM (8GB recommended)

### Automated Setup
```bash
# Clone the repository
git clone <repository-url>
cd ai-attendance-system

# Run automated setup
./setup.sh
```

### Manual Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create required directories
mkdir -p data/{faces,attendance,students} models logs

# Run database migrations
alembic upgrade head
```

## 📖 Usage

### 1. Build Face Database
```bash
# Add student face images to data/faces/{student_id}/
# Then build the recognition database
python scripts/build_face_database.py
```

### 2. Start Web Application
```bash
python app.py
```
Access at `http://localhost:5000`

**Default Credentials:**
- **Admin**: `admin@school.edu` / `admin456`
- **Teacher**: `teacher@school.edu` / `teacher123`
- **Student**: `student@school.edu` / `student123`

### 3. Real-time Attendance Capture
```python
from src.camera_pipeline.attendance_system import AttendanceSystem

# Initialize system
system = AttendanceSystem(camera_source=0)

# Start attendance session for class
system.start_session(class_id=1)

# Begin processing
system.run()
```

## ⚙️ Configuration

The system uses a centralized configuration system (`src/config.py`) with support for environment variables and JSON config files.

### Key Configuration Options

```python
# Camera settings
config.set('camera.resolution.width', 1280)
config.set('camera.fps', 30)

# Recognition thresholds
config.set('attendance.confidence_threshold', 0.7)
config.set('recognition.tolerance', 0.6)

# Liveness detection
config.set('liveness.enabled', True)
config.set('liveness.threshold', 0.6)
```

### Environment Variables
```bash
export ATTENDANCE_CAMERA_SOURCE=0
export ATTENDANCE_CONFIDENCE_THRESHOLD=0.7
export ATTENDANCE_DATABASE_URL="sqlite:///data/attendance.db"
```

## 🗄️ Database Schema

The system uses SQLAlchemy with the following core models:

- **User**: Multi-role users (Student/Teacher/Admin/Parent)
- **Class**: Academic classes/groups
- **Course**: Scheduled courses with time/room info
- **AttendanceSession**: Attendance capture sessions
- **AttendanceRecord**: Individual attendance entries
- **FaceEncoding**: Stored face embeddings
- **Announcement**: System announcements
- **SystemLog**: Audit logging

## 🔧 API Reference

### Authentication
```http
POST /api/auth/login
POST /api/auth/logout
```

### Attendance Management
```http
GET    /api/attendance/sessions
POST   /api/attendance/start
PUT    /api/attendance/stop
GET    /api/attendance/records
```

### User Management
```http
GET    /api/users
POST   /api/users
PUT    /api/users/{id}
DELETE /api/users/{id}
```

## 🧠 How It Works

### Face Detection Pipeline
1. **Camera Input**: Real-time video capture
2. **Face Detection**: YOLOv8 identifies faces with bounding boxes
3. **Liveness Check**: MediaPipe analyzes facial movements/blink detection
4. **Face Recognition**: FaceNet generates 128D embeddings for matching
5. **Attendance Logic**: Records attendance within time windows
6. **Database Storage**: Saves records with confidence scores

### Attendance Rules
- **Time Window**: First 5 minutes of class session
- **Confidence Threshold**: 70% minimum for automatic marking
- **Duplicate Prevention**: One record per student per session
- **Uncertain Matches**: Low-confidence detections flagged for review

## 🛠️ Development

### Code Quality
```bash
# Format code
make format

# Lint code
make lint

# Type check
make type-check

# Run tests
make test

# Full quality check
make quality
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "migration message"

# Apply migrations
alembic upgrade head
```

## 📊 Monitoring & Analytics

- **Performance Metrics**: FPS, processing latency, accuracy rates
- **Attendance Analytics**: Trends, patterns, predictions
- **System Health**: Database connections, memory usage
- **Fraud Detection**: ML-powered anomaly detection

## 🔒 Security

- **Authentication**: JWT tokens with role-based access control
- **Data Protection**: Bcrypt password hashing, secure file handling
- **Input Validation**: Comprehensive validation on all inputs
- **Audit Logging**: Complete system activity tracking

## 🚀 Deployment

### Production Setup
```bash
# Use Gunicorn for production
gunicorn -w 4 -b 0.0.0.0:8000 src.api:create_app()

# With PostgreSQL
export DATABASE_URL="postgresql://user:pass@localhost/attendance"

# Enable Redis caching
export REDIS_URL="redis://localhost:6379"
```

### Docker Support
```dockerfile
FROM python:3.11-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["python", "app.py"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with proper tests
4. Ensure code quality (`make quality`)
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 📞 Support

- **Documentation**: See `COMPLETE_GUIDE.md` for detailed setup
- **Issues**: Create GitHub issues for bugs/features
- **Discussions**: Use GitHub Discussions for questions

---

**Note**: This system is designed for educational institutions. Ensure compliance with privacy regulations (GDPR, FERPA, etc.) when deploying.
