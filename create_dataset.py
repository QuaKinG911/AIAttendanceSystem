#!/usr/bin/env python3
"""
Dataset Creator for AI Attendance System
Helps create and organize student face dataset
"""

import cv2
import os
import json
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from face_detection.yolo_detector import YOLOFaceDetector, HaarCascadeDetector
from utils.dataset_manager import add_student, load_students, get_student_dir, DATASET_DIR

class DatasetCreator:
    def __init__(self):
        self.dataset_dir = "data/faces"
        self.cap = None
        self.current_student = None
        
        # Initialize face detector with fallback
        try:
            self.face_detector = YOLOFaceDetector()
            print("✓ Using YOLO face detector")
        except Exception:
            self.face_detector = HaarCascadeDetector()
            print("✓ Using Haar Cascade face detector")
        
        # Create directories
        os.makedirs(self.dataset_dir, exist_ok=True)
        os.makedirs("data/face_encodings", exist_ok=True)
        
        print("🎓 AI Attendance System - Dataset Creator")
        print("=" * 50)
        print("This tool helps you create a student face dataset")
        print("for the AI attendance system.")
        print("=" * 50)
    
    def initialize_camera(self):
        """Initialize camera for photo capture"""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                print("❌ Failed to open camera")
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            
            print("✓ Camera initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Error initializing camera: {e}")
            return False
    
    def capture_student_photo(self, student_id, student_name):
        """Capture photo for a student using face detection"""
        print(f"\n📷 Capturing photo for: {student_name} ({student_id})")
        print("Position face in center of frame. Press 'c' to capture, 'q' to quit.")
        
        captured = False
        face_roi = None
        
        while not captured:
            ret, frame = self.cap.read()
            if not ret:
                print("❌ Failed to read from camera")
                break
            
            display_frame = frame.copy()
            
            # Face detection
            faces = self.face_detector.detect_faces_with_confidence(frame)
            
            detected_face_bbox = None
            if faces:
                # Find the largest face
                largest_face_area = 0
                for (x1, y1, x2, y2, conf) in faces:
                    area = (x2 - x1) * (y2 - y1)
                    if area > largest_face_area:
                        largest_face_area = area
                        detected_face_bbox = (x1, y1, x2, y2)
                
                if detected_face_bbox:
                    x1, y1, x2, y2 = detected_face_bbox
                    # Add some padding to the bounding box
                    padding = 20
                    x1 = max(0, x1 - padding)
                    y1 = max(0, y1 - padding)
                    x2 = min(frame.shape[1], x2 + padding)
                    y2 = min(frame.shape[0], y2 + padding)

                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(display_frame, "Face Detected", (x1, y1 - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    face_roi = frame[y1:y2, x1:x2]
                
                if len(faces) > 1:
                    cv2.putText(display_frame, "Multiple faces detected!", (10, 90), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                cv2.putText(display_frame, "No Face Detected", (10, 90), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Add instructions
            cv2.putText(display_frame, f"Student: {student_name}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(display_frame, "Press 'c' to capture", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.imshow('Dataset Creator - Capture', display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('c'):
                if face_roi is not None and face_roi.size > 0:
                    # Save photo
                    filename = f"{student_id}.jpg" # Standardize filename to student_id.jpg
                    filepath = os.path.join(self.dataset_dir, student_id, filename)
                    os.makedirs(os.path.join(self.dataset_dir, student_id), exist_ok=True)
                    
                    print(f"✓ Photo captured for {student_name} ({student_id})")
                    captured = True
                    return face_roi, f"{student_id}.jpg"
                else:
                    print("❌ No face detected to capture. Please ensure your face is visible.")
            elif key == ord('q'):
                break
        
        return None, None
    

    
    def create_from_existing_photos(self):
        """Create dataset from existing photos"""
        print("\n📁 Creating dataset from existing photos...")
        
        # Ask for photo directory
        photo_dir = input("Enter directory containing student photos: ").strip()
        
        if not os.path.exists(photo_dir):
            print("❌ Directory does not exist")
            return
        
        # Process each photo
        for filename in os.listdir(photo_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                filepath = os.path.join(photo_dir, filename)
                
                # Extract student info from filename
                # Expected format: StudentID_Name.jpg
                parts = filename.replace('.jpg', '').replace('.jpeg', '').replace('.png', '').split('_', 1)
                
                if len(parts) >= 2:
                    student_id = parts[0]
                    student_name = parts[1].replace('_', ' ')
                    
                    # Load and process image
                    img = cv2.imread(filepath)
                    if img is not None:
                        # Convert to bytes
                        is_success, im_buf_arr = cv2.imencode(".jpg", img)
                        if is_success:
                            image_bytes = im_buf_arr.tobytes()
                            ok, msg = add_student(student_id, student_name, image_bytes, '.jpg')
                            if ok:
                                print(f"✓ Processed: {student_name} ({student_id})")
                            else:
                                print(f"❌ Failed to add {student_name}: {msg}")
                        else:
                            print(f"❌ Failed to encode image for {filename}")
                    else:
                        print(f"❌ Failed to load: {filename}")
                else:
                    print(f"⚠️  Invalid filename format: {filename}")
        
        print(f"\n✅ Dataset created in: {self.dataset_dir}")
    
    def interactive_student_registration(self):
        """Interactive student registration"""
        print("\n👥 Interactive Student Registration")
        print("Enter student information (press Enter with empty ID to finish)")
        
        while True:
            student_id = input("\nStudent ID: ").strip()
            if not student_id:
                break
            
            student_name = input("Student Name: ").strip()
            if not student_name:
                print("❌ Name is required")
                continue
            
            # Check if already exists using dataset_manager
            students = load_students()
            if student_id in students:
                print(f"⚠️  Student {student_id} already exists")
                continue
            
            # Capture photo
            face_roi, filename = self.capture_student_photo(student_id, student_name)
            
            if face_roi is not None:
                # Convert numpy array to bytes for add_student
                is_success, im_buf_arr = cv2.imencode(".jpg", face_roi)
                if is_success:
                    image_bytes = im_buf_arr.tobytes()
                    ok, msg = add_student(student_id, student_name, image_bytes, '.jpg')
                    if ok:
                        print(f"✅ Student {student_name} registered successfully")
                    else:
                        print(f"❌ Failed to register {student_name}: {msg}")
                else:
                    print(f"❌ Failed to encode image for {student_name}")
            else:
                print(f"❌ Failed to register {student_name} (no photo captured)")
    
    def generate_dataset_report(self):
        """Generate dataset report"""
        students_data = load_students()
        
        if not students_data:
            print("❌ No student data found.")
            return
        
        student_list = list_students()
        
        print(f"\n📊 Dataset Report")
        print("=" * 30)
        print(f"Total Students: {len(student_list)}")
        print(f"Dataset Location: {DATASET_DIR}")
        print(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n👥 Student List:")
        for i, (student_id, name) in enumerate(student_list, 1):
            print(f"{i:2d}. {student_id} - {name}")
        
        # Save report
        report_file = os.path.join(DATASET_DIR, f"dataset_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with open(report_file, 'w') as f:
            f.write(f"AI Attendance System Dataset Report\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Students: {len(student_list)}\n\n")
            f.write("Student List:\n")
            for i, (student_id, name) in enumerate(student_list, 1):
                f.write(f"{i}. {student_id} - {name}\n")
        
        print(f"\n📄 Report saved: {report_file}")
    
    def run(self):
        """Main dataset creator interface"""
        print("\nChoose an option:")
        print("1. Interactive student registration (with camera)")
        print("2. Create dataset from existing photos")
        print("3. Generate dataset report")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == '1':
            if self.initialize_camera():
                self.interactive_student_registration()
                self.cap.release()
                cv2.destroyAllWindows()
        elif choice == '2':
            self.create_from_existing_photos()
        elif choice == '3':
            self.generate_dataset_report()
        elif choice == '4':
            print("👋 Goodbye!")
        else:
            print("❌ Invalid choice")

def main():
    """Main function"""
    creator = DatasetCreator()
    
    try:
        creator.run()
    except KeyboardInterrupt:
        print("\n⏹️ Dataset creation interrupted")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if creator.cap:
            creator.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()