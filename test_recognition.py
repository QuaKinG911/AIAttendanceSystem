#!/usr/bin/env python3
"""
Test face recognition with known faces
"""
import cv2
from src.face_recognition.matcher import FaceMatcher

def test_recognition():
    matcher = FaceMatcher()
    matcher.load_known_faces('data/face_encodings.pkl')

    print(f"Loaded {len(matcher.known_face_encodings)} known faces")

    # Test with a known face
    test_image_path = 'data/faces/hafid/hafid.jpg'
    image = cv2.imread(test_image_path)
    if image is None:
        print("Test image not found")
        return

    encoding = matcher.extract_face_features(image)
    if encoding is not None:
        print(f"Encoding shape: {encoding.shape}")
        student_id, name, conf = matcher.recognize_face(encoding)
        print(f"Recognition result: {student_id}, {name}, {conf}")
    else:
        print("Failed to extract encoding")

if __name__ == '__main__':
    test_recognition()