#!/usr/bin/env python3
"""
Add your face to the attendance system
"""

import cv2
import os
import sys
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def capture_face(student_id: str, student_name: str):
    """Capture face image and add to dataset"""
    print(f"🎥 Adding {student_name} ({student_id}) to the system")
    print("=" * 50)

    # Create student directory
    faces_dir = "data/faces"
    student_dir = os.path.join(faces_dir, student_id)
    os.makedirs(student_dir, exist_ok=True)

    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Camera not available")
        return False

    print("📷 Camera ready!")
    print("Position your face in the frame and press SPACE to capture")
    print("Press ESC to cancel")

    captured = False
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # Show frame
        cv2.imshow('Capture Face - Press SPACE to capture, ESC to cancel', frame)

        # Check for key press
        key = cv2.waitKey(1) & 0xFF

        if key == 32:  # SPACE key
            # Save the image
            image_path = os.path.join(student_dir, f"{student_id}.jpg")
            cv2.imwrite(image_path, frame)
            print(f"✅ Face captured and saved: {image_path}")
            captured = True
            break

        elif key == 27:  # ESC key
            print("❌ Capture cancelled")
            break

        # Auto-capture after 3 seconds if face is detected
        if frame_count > 90:  # ~3 seconds at 30fps
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = cv2.CascadeClassifier('models/haarcascade_frontalface_default.xml').detectMultiScale(gray, 1.1, 4)
            if len(faces) > 0:
                image_path = os.path.join(student_dir, f"{student_id}.jpg")
                cv2.imwrite(image_path, frame)
                print(f"✅ Face auto-captured and saved: {image_path}")
                captured = True
                break

    cap.release()
    cv2.destroyAllWindows()

    if captured:
        # Update students.json
        import json
        students_file = os.path.join(faces_dir, 'students.json')

        # Load existing students
        students = {}
        if os.path.exists(students_file):
            with open(students_file, 'r') as f:
                students = json.load(f)

        # Add new student
        students[student_id] = {"name": student_name}

        # Save updated students
        with open(students_file, 'w') as f:
            json.dump(students, f, indent=2)

        print(f"✅ Student {student_name} ({student_id}) added to dataset")

        # Regenerate face database
        print("\n🔄 Regenerating face database...")
        os.system('python create_face_database.py')

        return True

    return False

def main():
    import sys

    print("🎓 AI Attendance System - Add Your Face")
    print("=" * 50)

    # Get student info from command line arguments
    if len(sys.argv) < 3:
        print("Usage: python add_student.py <student_id> <student_name>")
        print("Example: python add_student.py STU001 'John Doe'")
        return

    student_id = sys.argv[1].strip()
    student_name = sys.argv[2].strip()

    if not student_id or not student_name:
        print("❌ Student ID and Name are required")
        return

    # Check if already exists
    students_file = "data/faces/students.json"
    if os.path.exists(students_file):
        import json
        with open(students_file, 'r') as f:
            students = json.load(f)
        if student_id in students:
            print(f"⚠️  Student {student_id} already exists. Use a different ID.")
            return

    print(f"Adding student: {student_name} ({student_id})")

    # Capture face
    if capture_face(student_id, student_name):
        print("\n🎉 Success! Your face has been added to the system.")
        print(f"   ID: {student_id}")
        print(f"   Name: {student_name}")
        print("\n🚀 Run the attendance system:")
        print("   python main.py")
        print("   Your face should now be recognized!")
    else:
        print("❌ Failed to add your face to the system")

if __name__ == "__main__":
    main()