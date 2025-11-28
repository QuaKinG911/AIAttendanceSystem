import cv2
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import threading
import queue

from src.face_detection.yolo_detector import YOLOFaceDetector
from src.face_recognition.matcher import FaceMatcher
from src.models import db, AttendanceSession, AttendanceRecord, AttendanceStatus, User
from src.config import config

class AttendanceSystem:
    def __init__(self, camera_source=0):
        self.camera_source = camera_source
        self.is_running = False
        self.frame_queue = queue.Queue(maxsize=10)
        self.result_queue = queue.Queue(maxsize=10)
        
        # Initialize components
        self.detector = YOLOFaceDetector(
            confidence_threshold=config.get('detection.confidence_threshold', 0.5)
        )
        self.matcher = FaceMatcher(
            tolerance=config.get('recognition.tolerance', 0.4),
            confidence_threshold=config.get('attendance.confidence_threshold', 0.5)
        )
        
        # Load known faces
        db_path = config.get('recognition.database_path', 'data/face_encodings.pkl')
        self.matcher.load_known_faces(db_path)
        
        # State tracking
        self.active_session_id = None
        self.processed_students = set()
        self.last_process_time = {}  # student_id -> timestamp
        
    def reload_face_database(self):
        """Reload the face recognition database"""
        db_path = config.get('recognition.database_path', 'data/face_encodings.pkl')
        self.matcher.load_known_faces(db_path)
        logging.info("Reloaded face recognition database")

    def start_session(self, class_id: int):
        """Start a new attendance session"""
        try:
            session = AttendanceSession(
                class_id=class_id,
                session_date=datetime.now().date(),
                start_time=datetime.now(),
                status='active'
            )
            db.session.add(session)
            db.session.commit()
            self.active_session_id = session.id
            self.processed_students.clear()
            logging.info(f"Started attendance session {self.active_session_id} for class {class_id}")
            return True
        except Exception as e:
            logging.error(f"Failed to start session: {e}")
            return False

    def stop_session(self):
        """Stop the current attendance session"""
        if self.active_session_id:
            try:
                session = AttendanceSession.query.get(self.active_session_id)
                if session:
                    session.end_time = datetime.now()
                    session.status = 'completed'
                    db.session.commit()
                self.active_session_id = None
                logging.info("Stopped attendance session")
            except Exception as e:
                logging.error(f"Failed to stop session: {e}")

    def process_frame(self, frame):
        """Process a single frame for attendance"""
        if not self.active_session_id:
            return frame

        # Detect faces
        faces = self.detector.detect_faces_with_confidence(frame)
        
        for (x1, y1, x2, y2, conf) in faces:
            # Extract face ROI with padding
            padding = 20
            h, w = frame.shape[:2]
            x1_pad = max(0, x1 - padding)
            y1_pad = max(0, y1 - padding)
            x2_pad = min(w, x2 + padding)
            y2_pad = min(h, y2 + padding)
            face_img = frame[y1_pad:y2_pad, x1_pad:x2_pad]
            if face_img.size == 0:
                continue
                
            # Recognize face
            face_encoding = self.matcher.extract_face_features(face_img)
            student_id, name, match_conf = self.matcher.recognize_face(face_encoding)

            # Debug logging
            if face_encoding is not None:
                logging.debug(f"Face encoding shape: {face_encoding.shape}, match_conf: {match_conf}")
            else:
                logging.debug("Failed to extract face encoding")

            # Draw bounding box and label
            color = (0, 255, 0) if name else (0, 0, 255)
            label = f"{name} ({match_conf:.2f})" if name else f"Unknown ({match_conf:.2f})"

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Record attendance if match is good and not already processed recently
            if name and student_id and match_conf >= config.get('attendance.confidence_threshold', 0.3):
                self._record_attendance(student_id, match_conf)

        return frame

    def _record_attendance(self, student_id, confidence):
        """Record attendance for a student"""
        now = datetime.now()
        
        # Debounce: Don't process same student too frequently (e.g., every 5 seconds)
        if student_id in self.last_process_time:
            if (now - self.last_process_time[student_id]).total_seconds() < 5:
                return

        self.last_process_time[student_id] = now
        
        # Check if already recorded for this session
        if student_id in self.processed_students:
            return

        try:
            # Create record
            record = AttendanceRecord(
                session_id=self.active_session_id,
                student_id=int(student_id), # Assuming ID is int in DB
                status=AttendanceStatus.PRESENT,
                detected_at=now,
                confidence_score=confidence
            )
            db.session.add(record)
            db.session.commit()
            
            self.processed_students.add(student_id)
            logging.info(f"Recorded attendance for student {student_id}")
            
        except Exception as e:
            logging.error(f"Failed to record attendance: {e}")
            db.session.rollback()

    def run(self):
        """Main loop for camera processing"""
        self.is_running = True
        cap = cv2.VideoCapture(self.camera_source)
        
        while self.is_running:
            ret, frame = cap.read()
            if not ret:
                break
                
            processed_frame = self.process_frame(frame)
            
            # Display (optional, mostly for debug or local view)
            cv2.imshow('Attendance System', processed_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        cap.release()
        cv2.destroyAllWindows()
        self.is_running = False
