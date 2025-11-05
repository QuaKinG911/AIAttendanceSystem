#!/usr/bin/env python3
"""
Integration tests for AI Attendance System
"""

import unittest
import sys
import os
import tempfile
import shutil
import numpy as np
import cv2
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()

        # Create test data directories
        os.makedirs(os.path.join(self.test_dir, 'data', 'faces'), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, 'data', 'face_encodings'), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, 'models'), exist_ok=True)

        # Change to test directory
        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    @patch('cv2.VideoCapture')
    def test_full_attendance_system_initialization(self, mock_video_capture):
        """Test full attendance system initialization"""
        from main import SimpleAttendanceSystem

        # Mock camera
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_WIDTH: 640,
            cv2.CAP_PROP_FRAME_HEIGHT: 480,
            cv2.CAP_PROP_FPS: 30
        }.get(prop, 0)
        mock_video_capture.return_value = mock_cap

        # Initialize system
        system = SimpleAttendanceSystem()

        self.assertIsNotNone(system)
        self.assertIsNotNone(system.face_detector)
        self.assertIsNotNone(system.face_matcher)

    def test_face_detection_pipeline(self):
        """Test the complete face detection pipeline"""
        from src.face_detection.yolo_detector import HaarCascadeDetector

        # Create test image with a simple rectangle (simulating a face)
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.rectangle(test_image, (25, 25), (75, 75), (255, 255, 255), -1)

        detector = HaarCascadeDetector()

        # Test detection
        faces = detector.detect_faces_with_confidence(test_image)

        # Should return some result (may be empty if cascade doesn't detect the rectangle)
        self.assertIsInstance(faces, list)

    def test_face_recognition_pipeline(self):
        """Test the complete face recognition pipeline"""
        from src.face_recognition.matcher import FaceMatcher

        matcher = FaceMatcher()

        # Create test face image
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        # Test feature extraction
        encoding = matcher.extract_face_features(test_image)

        # Should return some result (may be None if face_recognition fails)
        # The important thing is that it doesn't crash
        self.assertTrue(encoding is None or isinstance(encoding, np.ndarray))

    def test_dataset_manager_integration(self):
        """Test dataset manager integration"""
        from src.utils.dataset_manager import add_student, list_students, remove_student

        # Add a test student
        test_image = b'fake_image_data'
        success, path = add_student('TEST001', 'Test User', test_image)

        self.assertTrue(success)

        # List students
        students = list_students()
        self.assertEqual(len(students), 1)
        self.assertEqual(students[0], ('TEST001', 'Test User'))

        # Remove student
        success, message = remove_student('TEST001')
        self.assertTrue(success)

        # Verify removal
        students = list_students()
        self.assertEqual(len(students), 0)

    @patch('src.liveness_detection.mediapipe_liveness.mp')
    def test_liveness_detection_pipeline(self, mock_mp):
        """Test liveness detection pipeline"""
        from src.liveness_detection.mediapipe_liveness import MediaPipeLivenessDetector

        # Mock MediaPipe
        mock_face_mesh = MagicMock()
        mock_mp.solutions.face_mesh.FaceMesh.return_value = mock_face_mesh
        mock_mp.solutions.drawing_utils = MagicMock()

        detector = MediaPipeLivenessDetector()

        # Create test image and bbox
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        test_bbox = (25, 25, 75, 75)

        # Test detection
        result = detector.detect_liveness(test_image, test_bbox)

        self.assertIn('is_live', result)
        self.assertIn('liveness_score', result)
        self.assertIn('method', result)

    def test_configuration_integration(self):
        """Test configuration system integration"""
        from src.config import ConfigManager

        config = ConfigManager()

        # Test basic operations
        config.set('test.integration', 'working')
        self.assertEqual(config.get('test.integration'), 'working')

        # Test nested access
        config.set('camera.test.width', 1920)
        self.assertEqual(config.get('camera.test.width'), 1920)

    @patch('cv2.VideoCapture')
    def test_attendance_session_workflow(self, mock_video_capture):
        """Test a complete attendance session workflow"""
        from main import SimpleAttendanceSystem
        import time

        # Mock camera
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_video_capture.return_value = mock_cap

        system = SimpleAttendanceSystem()

        # Simulate session start
        system.session_start = time.time()
        system.attendance_duration = 0.1  # Very short for testing

        # Process a few frames
        for _ in range(3):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            processed = system.process_frame(frame)
            self.assertIsNotNone(processed)

        # Check that system didn't crash
        self.assertIsNotNone(system.attendance_records)


class TestPerformance(unittest.TestCase):
    """Performance tests for the system"""

    def setUp(self):
        """Set up performance test fixtures"""
        # Create a larger test image
        self.test_image = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)

    def test_face_detection_performance(self):
        """Test face detection performance"""
        from src.face_detection.yolo_detector import HaarCascadeDetector
        import time

        detector = HaarCascadeDetector()

        start_time = time.time()
        for _ in range(10):
            faces = detector.detect_faces_with_confidence(self.test_image)
        end_time = time.time()

        avg_time = (end_time - start_time) / 10
        # Should be reasonably fast (< 0.5 seconds per frame)
        self.assertLess(avg_time, 0.5, f"Face detection too slow: {avg_time:.3f}s per frame")

    def test_face_recognition_performance(self):
        """Test face recognition performance"""
        from src.face_recognition.matcher import FaceMatcher
        import time

        matcher = FaceMatcher()

        # Create test encoding
        test_encoding = np.random.rand(128).astype(np.float32)
        matcher.known_face_encodings = [test_encoding]
        matcher.known_face_ids = ['TEST001']
        matcher.known_face_names = ['Test User']

        start_time = time.time()
        for _ in range(10):
            result = matcher.recognize_face(test_encoding)
        end_time = time.time()

        avg_time = (end_time - start_time) / 10
        # Should be fast (< 0.1 seconds per recognition)
        self.assertLess(avg_time, 0.1, f"Face recognition too slow: {avg_time:.3f}s per recognition")


if __name__ == '__main__':
    # Set up logging for tests
    import logging
    logging.basicConfig(level=logging.WARNING)

    # Run tests
    unittest.main(verbosity=2)