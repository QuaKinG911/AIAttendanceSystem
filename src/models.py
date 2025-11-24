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
    PARENT = 'parent'

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
    username = Column(String(50), unique=True, nullable=True)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    full_name = Column(String(100))
    nationality = Column(String(50))
    gender = Column(String(1))  # 'M' or 'F'
    birthday = Column(Date)
    major = Column(String(100))  # For students
    degree_level = Column(String(20))  # Bachelor's, Master's, PhD
    start_year = Column(String(4))   # Year student started (e.g., '2023')
    courses = Column(JSON)       # For teachers, list of course names
    created_at = Column(DateTime, default=func.now())

    # Relationships
    enrollments = relationship('Enrollment', back_populates='student')
    attendance_records = relationship('AttendanceRecord', foreign_keys='AttendanceRecord.student_id', back_populates='student')
    logs = relationship('SystemLog', back_populates='user')

    __table_args__ = (
        db.Index('idx_user_email', 'email'),
        db.Index('idx_user_role', 'role'),
        db.Index('idx_user_username', 'username'),
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(str(self.password_hash), password)

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
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=False)
    name = Column(String(100), nullable=False)
    teacher_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    room = Column(String(50))
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    class_ = relationship('Class', back_populates='courses')
    teacher = relationship('User')

    __table_args__ = (
        db.CheckConstraint('day_of_week >= 0 AND day_of_week <= 6', name='check_day_of_week_range'),
        db.CheckConstraint('start_time < end_time', name='check_course_time_order'),
        db.Index('idx_course_class_teacher', 'class_id', 'teacher_id'),
        db.Index('idx_course_day_time', 'day_of_week', 'start_time', 'end_time'),
    )

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

class ParentStudent(db.Model):
    __tablename__ = 'parent_students'

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    student_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    relationship = Column(String(50), default='parent')  # parent, guardian, etc.
    is_primary_contact = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships - temporarily commented out due to SQLAlchemy issue
    # parent_user = relationship('User', foreign_keys=[parent_id])
    # student_user = relationship('User', foreign_keys=[student_id])

    __table_args__ = (
        db.UniqueConstraint('parent_id', 'student_id', name='unique_parent_student'),
        db.Index('idx_parent_student_parent', 'parent_id'),
        db.Index('idx_parent_student_student', 'student_id'),
    )

class AttendanceSession(db.Model):
    __tablename__ = 'attendance_sessions'

    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=False)
    session_date = Column(Date, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    status = Column(Enum(SessionStatus), default=SessionStatus.SCHEDULED, nullable=False)
    present_window_minutes = Column(Integer, default=5, nullable=False)  # Minutes after start for present
    late_window_minutes = Column(Integer, default=15, nullable=False)    # Minutes after present window for late

    # Relationships
    class_ = relationship('Class', back_populates='sessions')
    records = relationship('AttendanceRecord', back_populates='session')

    __table_args__ = (
        db.CheckConstraint('present_window_minutes > 0', name='check_present_window_positive'),
        db.CheckConstraint('late_window_minutes > 0', name='check_late_window_positive'),
        db.CheckConstraint('present_window_minutes < late_window_minutes', name='check_windows_order'),
        db.Index('idx_session_class_date', 'class_id', 'session_date'),
        db.Index('idx_session_status', 'status'),
    )

class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('attendance_sessions.id'), nullable=False)
    student_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(Enum(AttendanceStatus), nullable=False)
    detected_at = Column(DateTime)
    confidence_score = Column(DECIMAL(3, 2))
    liveness_score = Column(DECIMAL(3, 2))
    fraud_flags = Column(JSON)  # Store fraud detection results
    manual_override = Column(Boolean, default=False, nullable=False)
    override_by = Column(Integer, ForeignKey('users.id'))
    override_reason = Column(Text)

    # Relationships
    session = relationship('AttendanceSession', back_populates='records')
    student = relationship('User', foreign_keys=[student_id], back_populates='attendance_records')
    override_user = relationship('User', foreign_keys=[override_by])

    __table_args__ = (
        db.CheckConstraint('confidence_score >= 0 AND confidence_score <= 1', name='check_confidence_range'),
        db.CheckConstraint('liveness_score >= 0 AND liveness_score <= 1', name='check_liveness_range'),
        db.UniqueConstraint('session_id', 'student_id', name='unique_session_student'),
        db.Index('idx_record_session_student', 'session_id', 'student_id'),
        db.Index('idx_record_status', 'status'),
        db.Index('idx_record_detected_at', 'detected_at'),
    )

class FaceEncoding(db.Model):
    __tablename__ = 'face_encodings'

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    encoding = Column(LargeBinary, nullable=False)  # Store face encoding blob
    image_path = Column(String(255))
    created_at = Column(DateTime, default=func.now())

    # Relationships
    student = relationship('User')

    __table_args__ = (
        db.UniqueConstraint('student_id', name='unique_student_encoding'),
        db.Index('idx_encoding_student', 'student_id'),
    )

class Announcement(db.Model):
    __tablename__ = 'announcements'

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    target_audience = Column(String(50), default='all')  # all, students, teachers, parents
    priority = Column(String(20), default='normal')  # low, normal, high, urgent
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    author = relationship('User')

    __table_args__ = (
        db.Index('idx_announcement_active', 'is_active'),
        db.Index('idx_announcement_target', 'target_audience'),
        db.Index('idx_announcement_created', 'created_at'),
    )

class AttendanceAppeal(db.Model):
    __tablename__ = 'attendance_appeals'

    id = Column(Integer, primary_key=True)
    record_id = Column(Integer, ForeignKey('attendance_records.id'), nullable=False)
    student_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    parent_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    reason = Column(String(100), nullable=False)
    details = Column(Text)
    status = Column(String(20), default='pending')  # pending, approved, denied
    review_notes = Column(Text)
    reviewed_by = Column(Integer, ForeignKey('users.id'))
    reviewed_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    record = relationship('AttendanceRecord')
    student = relationship('User', foreign_keys=[student_id])
    parent = relationship('User', foreign_keys=[parent_id])
    reviewer = relationship('User', foreign_keys=[reviewed_by])

    __table_args__ = (
        db.Index('idx_appeal_status', 'status'),
        db.Index('idx_appeal_student', 'student_id'),
        db.Index('idx_appeal_created', 'created_at'),
    )

class SystemLog(db.Model):
    __tablename__ = 'system_logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    action = Column(String(100), nullable=False)
    details = Column(JSON)
    timestamp = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    user = relationship('User', back_populates='logs')

    __table_args__ = (
        db.Index('idx_log_user_timestamp', 'user_id', 'timestamp'),
        db.Index('idx_log_action', 'action'),
        db.Index('idx_log_timestamp', 'timestamp'),
    )