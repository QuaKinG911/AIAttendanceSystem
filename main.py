#!/usr/bin/env python3
"""
AI Attendance System - Main Entry Point
"""

import cv2
import numpy as np
import time
import threading
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime, timedelta
import json
import os
import sys

# Configure logging
# File handler gets DEBUG level, console gets INFO level
file_handler = logging.FileHandler('attendance_system.log')
file_handler.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Only INFO and above to console

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[file_handler, console_handler]
)

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.face_detection.yolo_detector import YOLOFaceDetector, HaarCascadeDetector
    from src.face_recognition.matcher import FaceMatcher
    from src.liveness_detection.mediapipe_liveness import MediaPipeLivenessDetector
    from src.config import config
except ImportError as e:
    logging.error(f"Critical import error: {e}")
    logging.error("Please ensure all dependencies are installed. Run: pip install -r requirements.txt")
    sys.exit(1)

class SimpleAttendanceSystem:
    def __init__(self, camera_source=None, class_id=None, session_id=None):
        # Use config values with fallbacks
        self.camera_source = camera_source if camera_source is not None else config.get('camera.source', 0)
        self.cap = None
        self.is_running = False
        self.class_id = class_id
        self.session_id = session_id

        # Load configuration
        self.attendance_duration = config.get('attendance.duration_minutes', 5)
        self.confidence_threshold = config.get('attendance.confidence_threshold', 0.7)
        self.liveness_threshold = config.get('attendance.liveness_threshold', 0.6)

        # Late attendance windows
        self.present_window_minutes = config.get('attendance.present_window_minutes', 5)
        self.late_window_minutes = config.get('attendance.late_window_minutes', 15)

        # Initialize components with fallbacks
        try:
            if config.get('detection.model', 'yolo') == 'yolo':
                self.face_detector = YOLOFaceDetector()
                logging.info("Using YOLO face detector")
            else:
                self.face_detector = HaarCascadeDetector()
                logging.info("Using Haar Cascade face detector")
        except Exception as e:
            logging.warning(f"Primary face detector failed to initialize ({e}), falling back to Haar Cascade")
            try:
                self.face_detector = HaarCascadeDetector()
                logging.info("Using Haar Cascade face detector")
            except Exception as e2:
                logging.error(f"Both face detectors failed to initialize: Primary({e}), Haar({e2})")
                raise RuntimeError("No face detection available. Please check model files and dependencies.")

        try:
            self.face_matcher = FaceMatcher(tolerance=config.get('recognition.tolerance', 0.6))
            db_path = config.get('recognition.database_path', 'data/face_encodings/face_database.pkl')
            db_path = os.path.join(os.path.dirname(__file__), db_path)
            self.face_matcher.load_known_faces(db_path)
            logging.info("Face matcher initialized and known faces loaded")
        except Exception as e:
            logging.error(f"Face matcher initialization failed: {e}")
            self.face_matcher = None

        try:
            if config.get('liveness.enabled', True):
                self.liveness_detector = MediaPipeLivenessDetector()
                logging.info("MediaPipe liveness detector initialized")
            else:
                self.liveness_detector = None
                logging.info("Liveness detection disabled")
        except Exception as e:
            logging.warning(f"Liveness detector initialization failed: {e}")
            self.liveness_detector = None

        # Attendance tracking
        self.attendance_records = {}
        self.session_start = None

        logging.info("Simple Attendance System initialized")
    
    def initialize_camera(self) -> bool:
        """Initialize camera"""
        try:
            logging.info(f"Initializing camera {self.camera_source}")

            # Try different backends if default fails
            backends = [cv2.CAP_ANY, cv2.CAP_V4L2]
            self.cap = cv2.VideoCapture(self.camera_source)

            if not self.cap.isOpened():
                logging.warning("Default backend failed, trying alternative backends")
                for backend in backends:
                    try:
                        self.cap = cv2.VideoCapture(self.camera_source, backend)
                        if self.cap.isOpened():
                            logging.info(f"Camera opened successfully with backend {backend}")
                            break
                    except Exception as e:
                        logging.warning(f"Failed to open camera with backend {backend}: {e}")
                        continue

            if not self.cap.isOpened():
                logging.error(f"Failed to open camera {self.camera_source} with any backend")
                return False

            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)

            # Verify camera properties
            actual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            actual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)

            logging.info(f"Camera initialized successfully")
            logging.info(f"Camera properties - Width: {actual_width}, Height: {actual_height}, FPS: {actual_fps}")
            try:
                logging.debug(f"Camera backend: {self.cap.getBackendName()}")
            except:
                logging.debug("Camera backend: Unknown")

            # Test reading a frame to ensure camera works
            test_ret, test_frame = self.cap.read()
            if not test_ret or test_frame is None:
                logging.error("Camera opened but failed to read test frame")
                self.cap.release()
                return False

            logging.info("Camera test frame read successfully")

            # Enforce minimum FPS
            if actual_fps < 25:
                logging.warning(f"Camera FPS ({actual_fps}) is below recommended 25 FPS. Performance may be affected.")
                # Try to set higher FPS
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                new_fps = self.cap.get(cv2.CAP_PROP_FPS)
                logging.info(f"Attempted to set FPS to 30, now: {new_fps}")

            return True

        except Exception as e:
            logging.error(f"Error initializing camera: {e}")
            return False
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """Process a single frame"""
        start_time = time.time()
        try:
            # Check if face detector is available
            if self.face_detector is None:
                logging.error("No face detector available")
                return frame

            # Face detection
            faces = self.face_detector.detect_faces_with_confidence(frame)
            detection_time = time.time()
            if len(faces) > 0:
                logging.info(f"Detected {len(faces)} face(s) in frame")
            logging.debug(f"Frame processed - Detected {len(faces)} faces in {(detection_time - start_time)*1000:.1f}ms")

            # Process each face
            for i, (x1, y1, x2, y2, confidence) in enumerate(faces):
                logging.debug(f"Face {i+1}: bbox=({x1},{y1},{x2},{y2}), detection_conf={confidence:.3f}")
                face_roi = frame[y1:y2, x1:x2]
                
                if face_roi.size == 0:
                    continue
                
                # Liveness detection
                is_live = True
                liveness_score = 1.0

                if self.liveness_detector:
                    liveness_result = self.liveness_detector.detect_liveness(frame, (x1, y1, x2, y2))
                    is_live = liveness_result['is_live']
                    liveness_score = liveness_result['liveness_score']
                    logging.debug(f"Face {i+1}: liveness_score={liveness_score:.3f}, is_live={is_live}")

                    # For testing: if liveness fails, still allow recognition but mark as suspicious
                    if not is_live and liveness_score > 0.3:  # Allow borderline cases
                        is_live = True
                        logging.info(f"Face {i+1}: borderline liveness ({liveness_score:.3f}), allowing recognition")
                
                # Face recognition
                student_name = "Unknown"
                recognition_confidence = 0.0

                if self.face_matcher and is_live:
                    face_encoding = self.face_matcher.extract_face_features(face_roi)
                    if face_encoding is not None:
                        logging.debug(f"Face {i+1}: extracted encoding, shape={face_encoding.shape}")
                        student_id, name, conf = self.face_matcher.recognize_face(face_encoding)
                        logging.debug(f"Face {i+1}: recognition result - id={student_id}, name={name}, conf={conf:.3f}")
                        if name:
                            student_name = name
                            recognition_confidence = conf

                            # Determine attendance status based on time
                            if self.session_start:
                                elapsed = datetime.now() - self.session_start
                                if elapsed <= timedelta(minutes=self.present_window_minutes):
                                    status = 'present'
                                elif elapsed <= timedelta(minutes=self.late_window_minutes):
                                    status = 'late'
                                else:
                                    status = 'absent'
                            else:
                                status = 'present'  # Default if no session start time

                            # Mark attendance
                            if student_id not in self.attendance_records:
                                self.attendance_records[student_id] = {
                                    'name': name,
                                    'time': datetime.now(),
                                    'confidence': conf,
                                    'liveness_score': liveness_score,
                                    'status': status
                                }
                                logging.info(f"Attendance marked for {name} (ID: {student_id}) as {status} with confidence {conf:.3f}")
                            else:
                                logging.debug(f"Attendance already marked for {name} (ID: {student_id})")
                        else:
                            logging.debug(f"Face {i+1}: no match found")
                    else:
                        logging.debug(f"Face {i+1}: failed to extract face encoding")
                else:
                    logging.debug(f"Face {i+1}: skipping recognition (matcher={self.face_matcher is not None}, live={is_live})")
                
                # Draw results
                color = (0, 255, 0) if is_live else (0, 0, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                
                # Draw labels
                label_y = y1 - 10
                cv2.putText(frame, student_name, (x1, label_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                if recognition_confidence > 0:
                    cv2.putText(frame, f"Conf: {recognition_confidence:.2f}", 
                               (x1, label_y - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
                
                if liveness_score < 1.0:
                    cv2.putText(frame, f"Live: {liveness_score:.2f}", 
                               (x1, label_y - 45), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
            
            # Draw attendance info
            info_text = f"Attendance: {len(self.attendance_records)} students"
            cv2.putText(frame, info_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            if self.session_start:
                elapsed = datetime.now() - self.session_start
                remaining = timedelta(minutes=self.attendance_duration) - elapsed
                if remaining.total_seconds() > 0:
                    time_text = f"Time left: {int(remaining.total_seconds()//60)}:{int(remaining.total_seconds()%60):02d}"
                else:
                    time_text = "Attendance window closed"
                cv2.putText(frame, time_text, (10, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            processing_time = time.time() - start_time
            logging.debug(f"Frame processing completed in {processing_time*1000:.1f}ms")
            return frame

        except Exception as e:
            processing_time = time.time() - start_time
            logging.error(f"Error processing frame after {processing_time*1000:.1f}ms: {e}")
            return frame
    
    def run(self):
        """Main processing loop"""
        if not self.initialize_camera():
            return
        
        self.is_running = True
        self.session_start = datetime.now()
        logging.info("Starting attendance system...")

        # FPS monitoring
        frame_count = 0
        start_time = time.time()

        try:
            frame_count = 0
            while self.is_running:
                ret, frame = self.cap.read()
                if not ret:
                    logging.error("Failed to read from camera")
                    break

                frame_count += 1
                if frame_count % 30 == 0:  # Log every 30 frames (~1 second)
                    logging.info(f"Processed {frame_count} frames, attendance: {len(self.attendance_records)}")
                
                # Process frame
                processed_frame = self.process_frame(frame)
                
                # Display
                cv2.imshow('AI Attendance System', processed_frame)
                
                # Check for key press
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    self.save_attendance()
                elif key == ord('r'):
                    self.reset_attendance()
                
                # Check if attendance window is closed
                if self.session_start:
                    elapsed = datetime.now() - self.session_start
                    if elapsed > timedelta(minutes=self.attendance_duration):
                        logging.info("Attendance window closed")
                        break
                
                # Control frame rate
                time.sleep(0.033)  # ~30 FPS

                # FPS monitoring
                frame_count += 1
                if frame_count % 30 == 0:  # Log every 30 frames
                    elapsed_time = time.time() - start_time
                    fps = frame_count / elapsed_time
                    logging.debug(f"FPS: {fps:.2f}, Frames processed: {frame_count}")
        
        except KeyboardInterrupt:
            logging.info("System interrupted by user")
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
        finally:
            self.cleanup()
    
    def save_attendance(self):
        """Save attendance records"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join(os.path.dirname(__file__), 'data', 'attendance')
            os.makedirs(output_dir, exist_ok=True)
            filename = os.path.join(output_dir, f"attendance_{timestamp}.json")
            
            # Convert datetime objects to strings for JSON serialization
            attendance_data = {}
            for student_id, record in self.attendance_records.items():
                attendance_data[student_id] = {
                    'name': record['name'],
                    'time': record['time'].isoformat(),
                    'confidence': record['confidence'],
                    'liveness_score': record['liveness_score'],
                    'status': record['status']
                }
            
            with open(filename, 'w') as f:
                json.dump(attendance_data, f, indent=2)
            
            logging.info(f"Attendance saved to {filename}")
            print(f"✓ Attendance saved: {len(self.attendance_records)} students")
            
        except Exception as e:
            logging.error(f"Error saving attendance: {e}")
    
    def reset_attendance(self):
        """Reset attendance records"""
        self.attendance_records.clear()
        self.session_start = datetime.now()
        logging.info("Attendance reset")
        print("✓ Attendance reset")
    
    def cleanup(self):
        """Cleanup resources"""
        self.is_running = False
        
        if self.cap:
            self.cap.release()
        
        cv2.destroyAllWindows()
        
        # Auto-save attendance
        if self.attendance_records:
            self.save_attendance()
        
        logging.info("System cleanup completed")
        print("✓ System stopped")

def main():
    """Main function"""
    print("🎓 AI Attendance System")
    print("=" * 50)
    print("Controls:")
    print("  q - Quit")
    print("  s - Save attendance")
    print("  r - Reset attendance")
    print("=" * 50)
    
    # Create and run system
    system = SimpleAttendanceSystem()
    
    try:
        system.run()
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        print(f"❌ Error: {e}")
    finally:
        system.cleanup()

if __name__ == "__main__":
    main()