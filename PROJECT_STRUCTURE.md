# AI Attendance System - Project Structure

## 📁 Organized Directory Structure

```
ai-attendance-system/
├── 📄 app.py                    # Main Flask application entry point
├── 📄 requirements.txt          # Python dependencies
├── 📄 .env                      # Environment configuration (not in git)
├── 📄 .env.example             # Example environment file
├── 📄 .gitignore               # Git ignore rules
├── 📄 README.md                # Project documentation
├── 📄 COMPLETE_GUIDE.md        # Complete setup guide
├── 📄 setup.sh                 # Automated setup script
├── 📄 run.sh                   # Quick run script
│
├── 📁 src/                     # Source code
│   ├── 📄 __init__.py
│   ├── 📄 models.py            # Database models (SQLAlchemy)
│   ├── 📄 config.py            # Application configuration
│   ├── 📄 security.py          # Security utilities
│   ├── 📄 cache.py             # Caching utilities
│   ├── 📄 email_service.py     # Email notifications
│   ├── 📄 ml_predictions.py    # ML prediction utilities
│   ├── 📄 performance.py       # Performance monitoring
│   │
│   ├── 📁 api/                 # REST API endpoints
│   │   ├── __init__.py         # API initialization
│   │   ├── auth.py             # Authentication API
│   │   ├── users.py            # User management API
│   │   ├── classes.py          # Class management API
│   │   ├── attendance.py       # Attendance API
│   │   ├── analytics.py        # Analytics API
│   │   └── admin.py            # Admin API
│   │
│   ├── 📁 web/                 # Web interface routes
│   │   ├── __init__.py
│   │   ├── auth.py             # Login/logout routes
│   │   ├── admin.py            # Admin dashboard routes
│   │   ├── student.py          # Student dashboard routes
│   │   ├── teacher.py          # Teacher dashboard routes
│   │   ├── parent.py           # Parent dashboard routes
│   │   └── common.py           # Common routes (profile, etc.)
│   │
│   ├── 📁 face_detection/      # Face detection module
│   │   └── yolo_detector.py
│   │
│   ├── 📁 face_recognition/    # Face recognition module
│   │   └── recognizer.py
│   │
│   ├── 📁 liveness_detection/  # Liveness detection
│   │   └── detector.py
│   │
│   ├── 📁 fraud_detection/     # Fraud detection
│   │   └── detector.py
│   │
│   ├── 📁 analytics/           # Analytics module
│   │   └── analyzer.py
│   │
│   ├── 📁 scheduling/          # Scheduling module
│   │   └── scheduler.py
│   │
│   └── 📁 utils/               # Utility functions
│       └── helpers.py
│
├── 📁 templates/               # HTML templates (Jinja2)
│   ├── base.html              # Base template
│   ├── login.html             # Login page
│   ├── profile.html           # User profile
│   │
│   ├── admin_*.html           # Admin pages (11 files)
│   ├── student_*.html         # Student pages (3 files)
│   ├── teacher_*.html         # Teacher pages (3 files)
│   └── parent_*.html          # Parent pages (1 file)
│
├── 📁 static/                  # Static assets
│   ├── css/                   # Stylesheets
│   ├── js/                    # JavaScript files
│   └── images/                # Images and icons
│
├── 📁 data/                    # Data storage
│   ├── attendance.db          # SQLite database
│   ├── faces/                 # Face images dataset
│   └── models/                # ML model files
│
├── 📁 scripts/                 # Utility scripts
│   ├── backup_database.py     # Database backup
│   ├── setup_models.py        # Download ML models
│   └── cron_backup.txt        # Cron job examples
│
├── 📁 alembic/                 # Database migrations
│   └── versions/              # Migration files
│
├── 📁 backups/                 # Database backups
│
├── 📁 logs/                    # Application logs
│
└── 📁 .cleanup_backup/         # Temporary backup of removed files
    └── YYYYMMDD_HHMMSS/       # Timestamped backup
```

## 🗑️ Files Removed (Moved to .cleanup_backup/)

### Log Files
- `*.log` - All log files (flask.log, server.log, attendance_system.log, etc.)
- `pip_install*.log` - Pip installation logs

### Utility/Test Scripts (moved to backup)
- `app_backup.py` - Backup of old app
- `test_app.py` - Test application
- `check_db.py` - Database checker
- `add_gender_field.py` - Migration script
- `add_student.py` - Student creation script
- `assign_teacher_courses.py` - Course assignment script
- `cleanup_database.py` - Database cleanup
- `cleanup_faces.py` - Face cleanup
- `create_dataset.py` - Dataset creation
- `create_face_database.py` - Face database creation
- `create_users.py` - User creation
- `debug_faces.py` - Face debugging
- `migrate_data.py` - Data migration
- `run_camera.py` - Camera test
- `run_tests.py` - Test runner
- `run_web.py` - Web runner
- `setup_semester_schedule.py` - Schedule setup
- `sync_face_dataset.py` - Face sync
- `test_attendance.py` - Attendance test
- `test_detection.py` - Detection test
- `test_streamlit.py` - Streamlit test
- `verify_system.py` - System verification

### Duplicate Files
- `src/models_new.py` - Duplicate model file

### Configuration Files (moved to backup)
- `nginx/` - Nginx configuration
- `nginx.conf` - Nginx config file
- `.venv311/` - Old virtual environment

## 📋 Key Files

### Core Application
- **app.py** - Main Flask application, registers blueprints, initializes database
- **requirements.txt** - All Python dependencies
- **.env** - Environment variables (SECRET_KEY, DATABASE_URL, etc.)

### Source Code
- **src/models.py** - Database models (User, Class, Course, Attendance, etc.)
- **src/api/** - REST API endpoints for frontend
- **src/web/** - Web routes for HTML pages

### Templates
- **templates/base.html** - Base template with navigation, styles
- **templates/admin_classes.html** - Fixed and styled admin classes page
- **templates/login.html** - Login page

## 🔧 No Code Changes Required

The cleanup only removed unused files and moved them to backup. All import paths remain the same:
- `from src.models import db, User, Class`
- `from src.api import create_app`
- `from src.web import web_admin_bp`

## ✅ Verification

After cleanup, the project structure is cleaner and more organized:
- ✅ All core functionality intact
- ✅ No broken imports
- ✅ Cleaner root directory
- ✅ Organized by purpose
- ✅ Backup of all removed files available

## 🚀 Running the Application

```bash
# Navigate to project
cd /home/quaking911/github/ai-attendance-system

# Run the application
python3 app.py

# Or use the run script
./run.sh
```

The application will start on http://127.0.0.1:5000

## 📝 Notes

- All removed files are safely backed up in `.cleanup_backup/`
- You can delete the backup folder after verifying everything works
- The project is now much cleaner and easier to navigate
- All functionality remains intact
