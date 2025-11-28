#!/usr/bin/env python3
"""
Build face recognition database from images in data/faces/
"""

import os
import sys
import cv2
import numpy as np
from pathlib import Path
import logging

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

try:
    from src.face_recognition.matcher import FaceMatcher
    from src.face_detection.yolo_detector import YOLOFaceDetector
    from src.utils.dataset_manager import list_students
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root")
    sys.exit(1)

def build_face_database():
    """Build face database from images"""

    # Setup logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    # Initialize components
    detector = YOLOFaceDetector()
    matcher = FaceMatcher()

    # Get students from dataset
    students = list_students()

    if not students:
        logging.warning("No students found in dataset. Please add student images first.")
        return False

    logging.info(f"Found {len(students)} students to process")

    processed_count = 0

    for student_id, student_name in students:
        print(f"Processing student: {student_name} (ID: {student_id})")

        # Get student directory
        from src.utils.dataset_manager import get_student_dir
        student_dir = get_student_dir(student_id)

        if not os.path.exists(student_dir):
            logging.warning(f"Student directory not found: {student_dir}")
            continue

        # Process all images for this student
        image_files = [f for f in os.listdir(student_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

        if not image_files:
            logging.warning(f"No images found for student {student_name}")
            continue

        student_encodings = []

        for image_file in image_files:
            image_path = os.path.join(student_dir, image_file)
            logging.info(f"Processing image: {image_path}")

            # Load image
            image = cv2.imread(image_path)
            if image is None:
                logging.error(f"Could not load image: {image_path}")
                continue

            # Detect faces
            faces = detector.detect_faces_with_confidence(image)

            if not faces:
                logging.warning(f"No faces detected in {image_path}")
                continue

            # Process each detected face
            for (x1, y1, x2, y2, conf) in faces:
                face_img = image[y1:y2, x1:x2]
                if face_img.size == 0:
                    continue

                # Extract features
                encoding = matcher.extract_face_features(face_img)
                if encoding is not None:
                    student_encodings.append(encoding)
                    logging.info(f"Extracted features from face in {image_file}")
                else:
                    logging.warning(f"Could not extract features from face in {image_file}")

        # Add to matcher if we got encodings
        if student_encodings:
            # Use the first encoding (or average them)
            avg_encoding = np.mean(student_encodings, axis=0)
            matcher.known_face_encodings.append(avg_encoding)
            matcher.known_face_ids.append(student_id)
            matcher.known_face_names.append(student_name)
            processed_count += 1
            logging.info(f"Added {student_name} to face database")
        else:
            logging.warning(f"No valid encodings for {student_name}")

    if processed_count > 0:
        # Save database
        db_path = 'data/face_encodings/face_database.pkl'
        print(f"Saving database to {db_path} with {processed_count} students")
        matcher.save_known_faces(db_path)
        print(f"Face database built successfully with {processed_count} students")
        return True
    else:
        print("No students could be processed")
        return False

if __name__ == '__main__':
    success = build_face_database()
    sys.exit(0 if success else 1)