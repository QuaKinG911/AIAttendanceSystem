from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()

class Student(Base):
    __tablename__ = 'students'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100))
    phone = Column(String(20))
    department = Column(String(100))
    face_encoding_path = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attendance_records = relationship("AttendanceRecord", back_populates="student")
    
    def __repr__(self):
        return f"<Student(id={self.id}, student_id='{self.student_id}', name='{self.name}')>"

class Class(Base):
    __tablename__ = 'classes'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    schedule = Column(String(100))  # e.g., "Mon-Wed-Fri 09:00-10:00"
    room = Column(String(50))
    camera_id = Column(String(50))
    instructor = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attendance_sessions = relationship("AttendanceSession", back_populates="class_info")
    
    def __repr__(self):
        return f"<Class(id={self.id}, name='{self.name}', room='{self.room}')>"

class AttendanceSession(Base):
    __tablename__ = 'attendance_sessions'
    
    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String(20), default='active')  # active, completed, cancelled
    total_students = Column(Integer, default=0)
    present_count = Column(Integer, default=0)
    absent_count = Column(Integer, default=0)
    uncertain_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    class_info = relationship("Class", back_populates="attendance_sessions")
    attendance_records = relationship("AttendanceRecord", back_populates="session")
    uncertain_matches = relationship("UncertainMatch", back_populates="session")
    
    def __repr__(self):
        return f"<AttendanceSession(id={self.id}, class_id={self.class_id}, status='{self.status}')>"

class AttendanceRecord(Base):
    __tablename__ = 'attendance_records'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('attendance_sessions.id'), nullable=False)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    confidence = Column(Float, nullable=False)
    status = Column(String(20), default='present')  # present, absent, late
    face_image_path = Column(String(255))
    liveness_score = Column(Float)
    detection_method = Column(String(50))  # yolo, haar, etc.
    recognition_method = Column(String(50))  # facenet, dlib, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    student = relationship("Student", back_populates="attendance_records")
    session = relationship("AttendanceSession", back_populates="attendance_records")
    
    def __repr__(self):
        return f"<AttendanceRecord(id={self.id}, student_id={self.student_id}, status='{self.status}')>"

class UncertainMatch(Base):
    __tablename__ = 'uncertain_matches'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('attendance_sessions.id'), nullable=False)
    face_image_path = Column(String(255), nullable=False)
    face_encoding = Column(Text)  # JSON string of face encoding
    confidence_scores = Column(Text)  # JSON string of potential matches
    timestamp = Column(DateTime, default=datetime.utcnow)
    admin_reviewed = Column(Boolean, default=False)
    admin_decision = Column(String(20))  # confirmed_present, confirmed_absent, false_positive
    admin_notes = Column(Text)
    reviewed_by = Column(String(100))
    reviewed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("AttendanceSession", back_populates="uncertain_matches")
    
    def __repr__(self):
        return f"<UncertainMatch(id={self.id}, reviewed={self.admin_reviewed})>"

class SystemLog(Base):
    __tablename__ = 'system_logs'
    
    id = Column(Integer, primary_key=True)
    level = Column(String(20), nullable=False)  # INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    module = Column(String(50))
    session_id = Column(Integer, ForeignKey('attendance_sessions.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<SystemLog(id={self.id}, level='{self.level}', module='{self.module}')>"

class CameraConfig(Base):
    __tablename__ = 'camera_configs'
    
    id = Column(Integer, primary_key=True)
    camera_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    ip_address = Column(String(50))
    port = Column(Integer)
    username = Column(String(50))
    password = Column(String(100))
    rtsp_url = Column(String(255))
    resolution_width = Column(Integer, default=1920)
    resolution_height = Column(Integer, default=1080)
    fps = Column(Integer, default=30)
    detection_zone = Column(Text)  # JSON string of polygon coordinates
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<CameraConfig(id={self.id}, camera_id='{self.camera_id}', active={self.is_active})>"

class DatabaseManager:
    def __init__(self, database_url: str = None):
        if database_url is None:
            # Default to SQLite for development
            database_url = f"sqlite:///data/attendance.db"
        
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def close_session(self, session):
        """Close database session"""
        session.close()
    
    def init_sample_data(self):
        """Initialize sample data for testing"""
        session = self.get_session()
        try:
            # Check if data already exists
            if session.query(Student).first() is None:
                # Add sample students
                students = [
                    Student(student_id="STU001", name="John Doe", email="john@example.com", department="Computer Science"),
                    Student(student_id="STU002", name="Jane Smith", email="jane@example.com", department="Engineering"),
                    Student(student_id="STU003", name="Bob Johnson", email="bob@example.com", department="Mathematics"),
                ]
                session.add_all(students)
                
                # Add sample class
                sample_class = Class(
                    name="Software Project Management",
                    description="Advanced software engineering course",
                    schedule="Mon-Wed-Fri 09:00-10:00",
                    room="Room 101",
                    camera_id="CAM001",
                    instructor="Dr. Smith"
                )
                session.add(sample_class)
                
                session.commit()
                print("Sample data initialized successfully")
            
        except Exception as e:
            session.rollback()
            print(f"Error initializing sample data: {e}")
        finally:
            self.close_session(session)

# Global database instance
db_manager = DatabaseManager()

def get_db():
    """Get database session (for dependency injection)"""
    session = db_manager.get_session()
    try:
        yield session
    finally:
        db_manager.close_session(session)