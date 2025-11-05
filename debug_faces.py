#!/usr/bin/env python3
"""
Debug face recognition issues
"""

import sys
import os
import cv2
import numpy as np

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.face_recognition.matcher import FaceMatcher

def debug_face_recognition():
    """Debug face recognition issues"""
    print("🔍 Face Recognition Debug")
    print("=" * 50)

    # Load face matcher
    matcher = FaceMatcher(tolerance=0.4)  # Lower tolerance
    db_path = 'data/face_encodings/face_database.pkl'

    if os.path.exists(db_path):
        matcher.load_known_faces(db_path)
        print(f"✅ Loaded {len(matcher.known_face_encodings)} faces from database")

        # Print known faces
        for i, (face_id, name) in enumerate(zip(matcher.known_face_ids, matcher.known_face_names)):
            print(f"  {i+1}. {name} ({face_id})")
    else:
        print(f"❌ Face database not found: {db_path}")
        return

    # Test with a sample image if available
    test_images = []
    faces_dir = 'data/faces'

    if os.path.exists(faces_dir):
        for student_dir in os.listdir(faces_dir):
            student_path = os.path.join(faces_dir, student_dir)
            if os.path.isdir(student_path):
                for file in os.listdir(student_path):
                    if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                        test_images.append((student_dir, os.path.join(student_path, file)))
                        break  # Just take first image per student

    print(f"\n🧪 Testing recognition with {len(test_images)} sample images:")

    for student_id, image_path in test_images:
        print(f"\nTesting {student_id} with image: {image_path}")

        # Load and process image
        image = cv2.imread(image_path)
        if image is None:
            print(f"  ❌ Could not load image")
            continue

        # Extract face encoding
        encoding = matcher.extract_face_features(image)
        if encoding is None:
            print(f"  ❌ Could not extract face encoding")
            continue

        print(f"  ✅ Extracted encoding (shape: {encoding.shape})")

        # Try recognition
        recognized_id, recognized_name, confidence = matcher.recognize_face(encoding)

        if recognized_id:
            match_status = "✅ MATCH" if recognized_id == student_id else "❌ WRONG MATCH"
            print(f"  {match_status}: {recognized_name} ({recognized_id}) - Confidence: {confidence:.3f}")
        else:
            print(f"  ❌ NO MATCH - Confidence: {confidence:.3f}")

if __name__ == "__main__":
    debug_face_recognition()