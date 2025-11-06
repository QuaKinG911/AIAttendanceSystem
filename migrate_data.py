#!/usr/bin/env python3
"""
Data Migration Script - Import existing JSON data into PostgreSQL
"""

import os
import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.models import db, User, Class, Enrollment, AttendanceSession, AttendanceRecord, FaceEncoding, UserRole
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = "sqlite:///data/attendance.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_test_data():
    """Create test data for development"""
    print("Creating test data...")

    session = SessionLocal()

    try:
        # Create admin user (check if exists first)
        admin = session.query(User).filter_by(username="admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@school.edu",
                role=UserRole.ADMIN
            )
            admin.set_password("admin123")
            session.add(admin)
            session.flush()

        # Create teacher (check if exists first)
        teacher = session.query(User).filter_by(username="teacher1").first()
        if not teacher:
            teacher = User(
                username="teacher1",
                email="teacher@school.edu",
                role=UserRole.TEACHER
            )
            teacher.set_password("teacher123")
            session.add(teacher)
            session.flush()

        # Create students (check if exists first)
        students = []
        for i in range(1, 6):
            student = session.query(User).filter_by(username=f"student{i}").first()
            if not student:
                student = User(
                    username=f"student{i}",
                    email=f"student{i}@school.edu",
                    role=UserRole.STUDENT
                )
                student.set_password("student123")
                session.add(student)
                session.flush()
            students.append(student)

        # Create class
        class1 = Class(
            name="Computer Science 101",
            teacher_id=teacher.id,
            start_time="09:00:00",
            end_time="10:30:00",
            present_window_minutes=5,
            late_window_minutes=15,
            room="Room 101"
        )
        session.add(class1)
        session.flush()

        # Enroll students
        for student in students:
            enrollment = Enrollment(
                class_id=class1.id,
                student_id=student.id
            )
            session.add(enrollment)

        session.commit()
        print("Test data created successfully")

    except Exception as e:
        session.rollback()
        print(f"Error creating test data: {e}")
    finally:
        session.close()

def migrate_attendance():
    """Migrate attendance data from JSON files"""
    print("Migrating attendance data...")

    attendance_dir = Path('data/attendance')
    if not attendance_dir.exists():
        print("No attendance directory found, skipping attendance migration")
        return

    session = SessionLocal()

    try:
        # First, create a default class if none exists
        default_class = session.query(Class).first()
        if not default_class:
            # Create a default teacher
            teacher = User(
                username="teacher1",
                email="teacher@school.edu",
                role=UserRole.TEACHER
            )
            teacher.set_password("password123")
            session.add(teacher)
            session.flush()

            default_class = Class(
                name="Default Class",
                teacher_id=teacher.id,
                start_time="09:00:00",
                end_time="10:00:00",
                present_window_minutes=5,
                late_window_minutes=15
            )
            session.add(default_class)
            session.flush()

        # Process attendance files
        for attendance_file in attendance_dir.glob('*.json'):
            print(f"Processing {attendance_file}")

            with open(attendance_file, 'r') as f:
                attendance_data = json.load(f)

            # Create attendance session
            session_date = datetime.now().date()  # Would need to parse from filename
            attendance_session = AttendanceSession(
                class_id=default_class.id,
                session_date=session_date,
                start_time=datetime.now(),
                status=AttendanceSession.SessionStatus.COMPLETED
            )
            session.add(attendance_session)
            session.flush()

            # Add attendance records
            for student_id, record in attendance_data.items():
                # Find user by username
                user = session.query(User).filter_by(username=student_id.lower()).first()
                if user:
                    attendance_record = AttendanceRecord(
                        session_id=attendance_session.id,
                        student_id=user.id,
                        status=AttendanceRecord.AttendanceStatus.PRESENT,  # Default to present
                        detected_at=datetime.fromisoformat(record['time']) if 'time' in record else datetime.now(),
                        confidence_score=record.get('confidence', 0.0),
                        liveness_score=record.get('liveness_score', 1.0)
                    )
                    session.add(attendance_record)

        session.commit()
        print("Attendance migration completed")

    except Exception as e:
        session.rollback()
        print(f"Error migrating attendance: {e}")
    finally:
        session.close()

def main():
    print("Starting data migration...")

    # Create tables if not exists
    db.metadata.create_all(bind=engine)

    create_test_data()

    print("Data migration completed!")

if __name__ == "__main__":
    main()