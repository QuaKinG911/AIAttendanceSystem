#!/usr/bin/env python3

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.models import db, User, UserRole
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = "sqlite:///data/attendance.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_admin():
    session = SessionLocal()
    try:
        # Create admin user
        admin = session.query(User).filter_by(username="admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@school.edu",
                role=UserRole.ADMIN
            )
            admin.set_password("admin456")
            session.add(admin)
            session.commit()
            print("Admin user created: admin/admin123")
        else:
            print("Admin user already exists")

        # Create a teacher
        teacher = session.query(User).filter_by(username="teacher1").first()
        if not teacher:
            teacher = User(
                username="teacher1",
                email="teacher@school.edu",
                role=UserRole.TEACHER
            )
            teacher.set_password("teacher123")
            session.add(teacher)
            session.commit()
            print("Teacher user created: teacher1/teacher123")

        # Create a student
        student = session.query(User).filter_by(username="student1").first()
        if not student:
            student = User(
                username="student1",
                email="student@school.edu",
                role=UserRole.STUDENT
            )
            student.set_password("student123")
            session.add(student)
            session.commit()
            print("Student user created: student1/student123")

    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    create_admin()