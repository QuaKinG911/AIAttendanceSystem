#!/bin/bash
# Project Cleanup Script
# This script removes unnecessary files and organizes the project structure

echo "🧹 Starting AI Attendance System Cleanup..."

# Create a cleanup directory for files we're removing (just in case)
mkdir -p .cleanup_backup
BACKUP_DIR=".cleanup_backup/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📦 Backing up files to $BACKUP_DIR before deletion..."

# 1. Remove log files (keep them in backup)
echo "Removing log files..."
find . -maxdepth 1 -name "*.log" -type f -exec mv {} "$BACKUP_DIR/" \;

# 2. Remove pip installation logs
echo "Removing pip installation logs..."
find . -maxdepth 1 -name "pip_install*.log" -type f -exec mv {} "$BACKUP_DIR/" \;

# 3. Remove backup/test Python scripts
echo "Removing backup and utility scripts..."
mv app_backup.py "$BACKUP_DIR/" 2>/dev/null || true
mv test_app.py "$BACKUP_DIR/" 2>/dev/null || true
mv check_db.py "$BACKUP_DIR/" 2>/dev/null || true
mv add_gender_field.py "$BACKUP_DIR/" 2>/dev/null || true
mv add_student.py "$BACKUP_DIR/" 2>/dev/null || true
mv assign_teacher_courses.py "$BACKUP_DIR/" 2>/dev/null || true
mv cleanup_database.py "$BACKUP_DIR/" 2>/dev/null || true
mv cleanup_faces.py "$BACKUP_DIR/" 2>/dev/null || true
mv create_dataset.py "$BACKUP_DIR/" 2>/dev/null || true
mv create_face_database.py "$BACKUP_DIR/" 2>/dev/null || true
mv create_users.py "$BACKUP_DIR/" 2>/dev/null || true
mv debug_faces.py "$BACKUP_DIR/" 2>/dev/null || true
mv migrate_data.py "$BACKUP_DIR/" 2>/dev/null || true
mv run_camera.py "$BACKUP_DIR/" 2>/dev/null || true
mv run_tests.py "$BACKUP_DIR/" 2>/dev/null || true
mv run_web.py "$BACKUP_DIR/" 2>/dev/null || true
mv setup_semester_schedule.py "$BACKUP_DIR/" 2>/dev/null || true
mv sync_face_dataset.py "$BACKUP_DIR/" 2>/dev/null || true
mv test_attendance.py "$BACKUP_DIR/" 2>/dev/null || true
mv test_detection.py "$BACKUP_DIR/" 2>/dev/null || true
mv test_streamlit.py "$BACKUP_DIR/" 2>/dev/null || true
mv verify_system.py "$BACKUP_DIR/" 2>/dev/null || true

# 4. Remove duplicate model files
echo "Removing duplicate model files..."
mv src/models_new.py "$BACKUP_DIR/" 2>/dev/null || true

# 5. Remove empty/unused directories
echo "Checking for empty directories..."
find . -type d -empty -not -path "./.git/*" -not -path "./.cleanup_backup/*" 2>/dev/null

# 6. Remove __pycache__ directories
echo "Removing Python cache directories..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# 7. Clean up old virtual environment if exists
if [ -d ".venv311" ]; then
    echo "Removing old virtual environment..."
    mv .venv311 "$BACKUP_DIR/" 2>/dev/null || true
fi

# 8. Remove nginx config if not using nginx
if [ -d "nginx" ]; then
    echo "Moving nginx config to backup..."
    mv nginx "$BACKUP_DIR/" 2>/dev/null || true
    mv nginx.conf "$BACKUP_DIR/" 2>/dev/null || true
fi

# 9. Remove monitoring if not configured
if [ -d "monitoring" ] && [ -z "$(ls -A monitoring 2>/dev/null)" ]; then
    echo "Removing empty monitoring directory..."
    rmdir monitoring 2>/dev/null || true
fi

# 10. Remove instance directory if empty
if [ -d "instance" ] && [ -z "$(ls -A instance 2>/dev/null)" ]; then
    echo "Removing empty instance directory..."
    rmdir instance 2>/dev/null || true
fi

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📊 Summary:"
echo "  - Log files moved to backup"
echo "  - Utility scripts moved to backup"
echo "  - Python cache cleaned"
echo "  - Duplicate files removed"
echo ""
echo "💾 Backup location: $BACKUP_DIR"
echo "   (You can delete this folder after verifying everything works)"
echo ""
echo "📁 Organized project structure:"
echo "  ├── app.py              (Main application)"
echo "  ├── requirements.txt    (Dependencies)"
echo "  ├── .env               (Configuration)"
echo "  ├── src/               (Source code)"
echo "  ├── templates/         (HTML templates)"
echo "  ├── static/            (CSS, JS, images)"
echo "  ├── data/              (Database & datasets)"
echo "  └── scripts/           (Utility scripts)"
