import os
import sys
import cv2
import numpy as np
import logging

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.face_recognition.matcher import FaceMatcher
from src.utils.dataset_manager import load_students, get_student_dir, DATASET_DIR

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_face_database(output_path: str):
    logging.info("Starting face database creation...")
    
    matcher = FaceMatcher()
    students = load_students()

    if not students:
        logging.warning("No students found in students.json. Please add students first.")
        return

    for student_id, student_info in students.items():
        student_name = student_info.get('name', 'Unknown')
        if not student_name:
            student_name = 'Unknown'
        student_dir = get_student_dir(student_id)
        
        # Assuming the primary image is named after the student_id with a .jpg extension
        image_path = os.path.join(student_dir, f"{student_id}.jpg")

        if not os.path.exists(image_path):
            logging.warning(f"Image not found for student {student_name} ({student_id}) at {image_path}. Skipping.")
            continue

        try:
            face_image = cv2.imread(image_path)
            if face_image is None:
                logging.error(f"Could not read image {image_path} for student {student_name}. Skipping.")
                continue
            
            # FaceMatcher's add_known_face expects a face_image (ROI), not the full image.
            # We need to detect the face in the image first.
            # For simplicity, let's assume the image provided is already a cropped face or contains one clear face.
            # In a real scenario, you'd use a face detector here.
            # For now, we'll pass the whole image and let extract_face_features handle it.
            # If face_recognition.face_encodings is used, it will detect faces.
            # If simple features are used, it will resize the whole image.

            if matcher.add_known_face(face_image, student_id, student_name):
                logging.info(f"Added {student_name} ({student_id}) to known faces.")
            else:
                logging.warning(f"Failed to add {student_name} ({student_id}) to known faces.")

        except Exception as e:
            logging.error(f"Error processing image for {student_name} ({student_id}): {e}")
            continue

    matcher.save_known_faces(output_path)
    logging.info(f"Face database created and saved to {output_path}")

if __name__ == "__main__":
    output_file = os.path.join(os.path.dirname(__file__), 'data', 'face_encodings', 'face_database.pkl')
    create_face_database(output_file)
