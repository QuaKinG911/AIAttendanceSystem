# src/models.py - Database Models for AI Attendance System

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, DECIMAL, JSON, Enum, Date, Time, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash
import enum

db = SQLAlchemy()

class UserRole(enum.Enum):
    STUDENT = 'student'
    TEACHER = 'teacher'
    ADMIN = 'admin'

class AttendanceStatus(enum.Enum):
    PRESENT = 'present'
    LATE = 'late'
    ABSENT = 'absent'

class SessionStatus(enum.Enum):
    SCHEDULED = 'scheduled'
    ACTIVE = 'active'
    COMPLETED = 'completed'

class User(db.Model):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    enrollments = relationship('Enrollment', back_populates='student')
    attendance_records = relationship('AttendanceRecord', foreign_keys='AttendanceRecord.student_id', back_populates='student')
    logs = relationship('SystemLog', back_populates='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Class(db.Model):
    __tablename__ = 'classes'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    courses = relationship('Course', back_populates='class_')
    enrollments = relationship('Enrollment', back_populates='class_')
    sessions = relationship('AttendanceSession', back_populates='class_')

class Course(db.Model):
    __tablename__ = 'courses'

    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey('classes.id'))
    name = Column(String(100), nullable=False)
    teacher_id = Column(Integer, ForeignKey('users.id'))
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    room = Column(String(50))
    day_of_week = Column(Integer)  # 0=Monday, 6=Sunday
    created_at = Column(DateTime, default=func.now())

    # Relationships
    class_ = relationship('Class', back_populates='courses')
    teacher = relationship('User')

class Enrollment(db.Model):
    __tablename__ = 'enrollments'

    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey('classes.id'))
    student_id = Column(Integer, ForeignKey('users.id'))
    enrolled_at = Column(DateTime, default=func.now())

    # Relationships
    class_ = relationship('Class', back_populates='enrollments')
    student = relationship('User', back_populates='enrollments')

    __table_args__ = (
        db.UniqueConstraint('class_id', 'student_id', name='unique_enrollment'),
    )

class AttendanceSession(db.Model):
    __tablename__ = 'attendance_sessions'

    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey('classes.id'))
    session_date = Column(Date, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    status = Column(Enum(SessionStatus), default=SessionStatus.SCHEDULED)

    # Relationships
    class_ = relationship('Class', back_populates='sessions')
    records = relationship('AttendanceRecord', back_populates='session')

class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('attendance_sessions.id'))
    student_id = Column(Integer, ForeignKey('users.id'))
    status = Column(Enum(AttendanceStatus), nullable=False)
    detected_at = Column(DateTime)
    confidence_score = Column(DECIMAL(3, 2))
    liveness_score = Column(DECIMAL(3, 2))
    fraud_flags = Column(JSON)  # Store fraud detection results
    manual_override = Column(Boolean, default=False)
    override_by = Column(Integer, ForeignKey('users.id'))
    override_reason = Column(Text)

    # Relationships
    session = relationship('AttendanceSession', back_populates='records')
    student = relationship('User', foreign_keys=[student_id], back_populates='attendance_records')
    override_user = relationship('User', foreign_keys=[override_by])

class FaceEncoding(db.Model):
    __tablename__ = 'face_encodings'

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('users.id'))
    encoding = Column(LargeBinary, nullable=False)  # Store face encoding blob
    image_path = Column(String(255))
    created_at = Column(DateTime, default=func.now())

    # Relationships
    student = relationship('User')

class SystemLog(db.Model):
    __tablename__ = 'system_logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String(100), nullable=False)
    details = Column(JSON)
    timestamp = Column(DateTime, default=func.now())

    # Relationships
    user = relationship('User', back_populates='logs')