# AI Attendance System - Agent Guidelines

## Project Overview
AI-powered attendance tracking system using computer vision. Python 3.11, Flask web framework, SQLAlchemy ORM, face recognition with YOLOv8/OpenCV, liveness detection with MediaPipe. Multi-role system (Admin/Teacher/Student/Parent) with real-time camera processing, database integration, and comprehensive monitoring.

## Technology Stack
- **Language**: Python 3.11
- **Web Framework**: Flask 2.3.3 with blueprints, JWT auth, SocketIO
- **Database**: SQLAlchemy 2.0.21 (SQLite/PostgreSQL), Alembic migrations
- **Computer Vision**: OpenCV 4.8.1, face-recognition 1.3.0, ultralytics YOLOv8, MediaPipe
- **ML/AI**: PyTorch, scikit-learn, XGBoost, joblib for model serialization
- **Data Processing**: NumPy, pandas, matplotlib, seaborn
- **Async/Background**: Celery 5.3.4, Redis 5.0.1, APScheduler 3.10.4
- **Communication**: Twilio SMS, SendGrid email, Flask-Mail
- **Security**: bcrypt, flask-limiter, werkzeug security
- **Monitoring**: Prometheus metrics, performance monitoring
- **UI**: Flask templates (Jinja2), Streamlit 1.37.1 dashboard
- **Deployment**: Gunicorn 21.2.0, Docker-ready

## Build/Test Commands
- **Install dev deps**: `make install` or `pip install black isort ruff mypy pytest pytest-cov`
- **Format code**: `make format` (black + isort, line length 100)
- **Lint**: `make lint` (ruff with E, W, F, I, B, C4, UP rules)
- **Type check**: `make type-check` (mypy strict mode)
- **Run all tests**: `make test` (pytest via run_tests.py)
- **Run single test**: `python -m pytest tests/test_file.py::TestClass::test_method -v`
- **Quality check**: `make quality` (format + lint + type-check + test)
- **Clean cache**: `make clean` (removes __pycache__, .mypy_cache, .pytest_cache)

## Code Style Guidelines
- **Formatting**: Black (100 char lines), isort (black profile, multi-line output 3)
- **Imports**: Group stdlib, third-party, local; absolute imports only; trailing comma + multi-line
- **Types**: Strict mypy - type hints required, avoid Any, handle Optional properly, no implicit optional
- **Naming**: snake_case functions/variables, PascalCase classes, UPPER_CASE constants
- **Error handling**: Specific exceptions in try/except, context logging, no bare except
- **Docstrings**: Google/NumPy style for all public functions, classes, modules
- **Security**: Never log sensitive data, validate inputs, parameterized queries, bcrypt passwords
- **Performance**: Use caching (Redis), async processing, batch operations, connection pooling

## Project Structure & Architecture
- `src/` - Main application code (Flask blueprints, API endpoints, ML pipelines)
- `ui/` - Streamlit dashboard interface
- `data/` - Student photos, attendance records, face database
- `templates/` - Jinja2 HTML templates for web interface
- `static/` - CSS/JS/images assets
- `alembic/` - Database migrations (7 versions: initial schema, courses, dates, constraints)
- `monitoring/` - Prometheus configuration
- `scripts/` - Database backup, cron jobs, model setup utilities

## Development Workflow
1. **Setup**: `./setup.sh` (installs deps, creates dirs, downloads models)
2. **Development**: `python app.py` (Flask dev server) or `streamlit run ui/streamlit_app.py`
3. **Camera Processing**: `python run_camera.py` (attendance capture with class ID)
4. **Database**: `alembic upgrade head` (apply migrations), `alembic revision --autogenerate` (new migrations)
5. **Testing**: pytest with coverage (currently no tests directory - needs creation)
6. **Quality**: `make quality` before commits
7. **Backup**: `python scripts/backup_database.py` (automated via cron)

## Key Components
- **Face Detection**: YOLOv8 primary, OpenCV Haar cascade fallback
- **Face Recognition**: FaceNet embeddings, Dlib landmarks, cosine similarity matching
- **Liveness Detection**: MediaPipe face mesh analysis, anti-spoofing
- **Attendance Logic**: 5-minute window, confidence thresholds, uncertain match flagging
- **User Management**: JWT authentication, role-based access (Student/Teacher/Admin/Parent)
- **Real-time Processing**: Camera pipeline with multi-threading, WebSocket updates
- **Analytics**: ML predictions, performance metrics, fraud detection

## Configuration & Environment
- **Config**: `config/settings.json` + environment variables (.env file)
- **Database**: SQLite default (attendance.db), PostgreSQL production-ready
- **Models**: Auto-downloaded (YOLOv8, MediaPipe), cached in models/ directory
- **Security**: Input validation, rate limiting, secure file handling
- **Monitoring**: Prometheus metrics, system logs, performance tracking

## Deployment & Production
- **WSGI**: Gunicorn with config tuning
- **Database**: PostgreSQL with connection pooling
- **Cache**: Redis for session/cache storage
- **Background Jobs**: Celery workers for async processing
- **Monitoring**: Prometheus + Grafana dashboard
- **Backup**: Automated database dumps, cron scheduling
- **Security**: HTTPS, input sanitization, CSRF protection

## No Cursor/Copilot Rules Found
No .cursor/rules/ or .cursorrules files detected. No .github/copilot-instructions.md found.