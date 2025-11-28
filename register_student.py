#!/usr/bin/env python3

import cv2
import os
import sys
import pickle
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from face_recognition.matcher import FaceMatcher
except ImportError:
    print("❌ Face recognition module not available")
    sys.exit(1)

def register_student():
    """Register a new student"""
    print("🎓 Student Registration")
    print("=======================")
    
    # Get student information
    student_id = input("Enter Student ID: ").strip()
    name = input("Enter Student Name: ").strip()
    email = input("Enter Email (optional): ").strip()
    
    if not student_id or not name:
        print("❌ Student ID and Name are required")
        return
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Failed to open camera")
        return
    
    print("\n📷 Position your face in the camera frame")
    print("Press 'c' to capture, 'q' to quit")
    
    face_matcher = FaceMatcher()
    
    # Load existing database
    db_path = "data/face_database.pkl"
    if os.path.exists(db_path):
        face_matcher.load_known_faces(db_path)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Display frame
        cv2.imshow('Student Registration', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('c'):
            # Capture face
            success = face_matcher.add_known_face(frame, student_id, name)
            if success:
                print(f"✓ Student {name} registered successfully")
                
                # Save database
                face_matcher.save_known_faces(db_path)
                
                # Save face image
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"data/students/{student_id}_{name.replace(' ', '_')}_{timestamp}.jpg"
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                
                cv2.imwrite(filename, frame)
                print(f"✓ Face image saved: {filename}")
                
                break
            else:
                print("❌ Failed to register face. Please try again.")
        
        elif key == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    register_student()
