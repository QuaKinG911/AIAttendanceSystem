#!/usr/bin/env python3
"""
Quick test of face detection
"""

import sys
import os
import cv2

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.face_detection.yolo_detector import YOLOFaceDetector

def test_face_detection():
    """Test face detection with camera"""
    print("🧪 Testing Face Detection...")
    print("=" * 40)

    # Initialize detector
    detector = YOLOFaceDetector()

    # Try to open camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not open camera")
        return

    print("✅ Camera opened successfully")
    print("📷 Testing face detection for 5 seconds...")
    print("Press Ctrl+C to stop early")

    import time
    start_time = time.time()
    frame_count = 0
    face_count = 0

    try:
        while time.time() - start_time < 5:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1

            # Detect faces
            faces = detector.detect_faces_with_confidence(frame)
            face_count += len(faces)

            if faces:
                print(f"  📍 Frame {frame_count}: Detected {len(faces)} face(s)")
                for i, (x1, y1, x2, y2, conf) in enumerate(faces):
                    print(".2f")

            time.sleep(0.1)  # Small delay

    except KeyboardInterrupt:
        pass
    finally:
        cap.release()

    print("\n📊 Test Results:")
    print(f"  • Frames processed: {frame_count}")
    print(f"  • Total faces detected: {face_count}")
    print(f"  • Average faces per frame: {face_count/frame_count:.2f}" if frame_count > 0 else "  • No frames processed")

    if face_count > 0:
        print("✅ Face detection is working!")
    else:
        print("⚠️  No faces detected - check camera/lighting")

if __name__ == "__main__":
    test_face_detection()