# src/scheduling/__init__.py - Automated scheduling system

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, time
import logging
from src.models import db, Class, AttendanceSession, SessionStatus
# from main import SimpleAttendanceSystem  # Commented out due to cv2 dependency

class SimpleAttendanceSystem:
    """Stub class for attendance system"""
    def __init__(self, class_id=None, session_id=None):
        self.class_id = class_id
        self.session_id = session_id

    def initialize_camera(self):
        pass

    def cleanup(self):
        pass

scheduler = BackgroundScheduler()
attendance_systems = {}  # Track active systems

def start_class_session(class_id):
    """Start attendance session for a class"""
    logging.info(f"Starting attendance session for class {class_id}")

    # Create database session
    session = AttendanceSession(
        class_id=class_id,
        session_date=datetime.now().date(),
        start_time=datetime.now(),
        status=SessionStatus.ACTIVE
    )

    db.session.add(session)
    db.session.commit()

    # Start attendance system
    system = SimpleAttendanceSystem(class_id=class_id, session_id=session.id)
    attendance_systems[class_id] = system

    try:
        system.initialize_camera()
        # Note: In production, this would run in a separate thread/process
        # For now, we'll just mark as started
        logging.info(f"Attendance system started for class {class_id}")
    except Exception as e:
        logging.error(f"Failed to start attendance for class {class_id}: {e}")

def end_class_session(class_id):
    """End attendance session for a class"""
    logging.info(f"Ending attendance session for class {class_id}")

    if class_id in attendance_systems:
        system = attendance_systems[class_id]
        system.cleanup()
        del attendance_systems[class_id]

    # Update database session
    session = AttendanceSession.query.filter_by(
        class_id=class_id,
        session_date=datetime.now().date(),
        status=SessionStatus.ACTIVE
    ).first()

    if session:
        session.end_time = datetime.now()
        session.status = SessionStatus.COMPLETED
        db.session.commit()

def schedule_class_sessions():
    """Schedule attendance sessions for all classes"""
    classes = Class.query.all()

    for class_obj in classes:
        # Schedule start time (e.g., 5 minutes before class starts)
        start_trigger = CronTrigger(
            hour=class_obj.start_time.hour,
            minute=max(0, class_obj.start_time.minute - 5)
        )

        # Schedule end time
        end_trigger = CronTrigger(
            hour=class_obj.end_time.hour,
            minute=class_obj.end_time.minute
        )

        # Add jobs
        scheduler.add_job(
            func=start_class_session,
            trigger=start_trigger,
            args=[class_obj.id],
            id=f'start_class_{class_obj.id}',
            replace_existing=True
        )

        scheduler.add_job(
            func=end_class_session,
            trigger=end_trigger,
            args=[class_obj.id],
            id=f'end_class_{class_obj.id}',
            replace_existing=True
        )

def init_scheduler():
    """Initialize the scheduler"""
    scheduler.start()
    schedule_class_sessions()
    logging.info("Scheduler initialized and class sessions scheduled")

def shutdown_scheduler():
    """Shutdown the scheduler"""
    try:
        if scheduler.running:
            scheduler.shutdown()
            logging.info("Scheduler shutdown")
        else:
            logging.info("Scheduler was not running")
    except Exception as e:
        logging.warning(f"Scheduler shutdown error: {e}")