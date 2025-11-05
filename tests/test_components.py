#!/usr/bin/env python3
"""
Unit tests for AI Attendance System components
"""

import unittest
import sys
import os
import numpy as np
import cv2
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestFaceDetection(unittest.TestCase):
    """Test face detection components"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a mock image
        self.test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

    @patch('cv2.CascadeClassifier')
    def test_haar_detector_initialization(self, mock_cascade):
        """Test Haar cascade detector initialization"""
        from src.face_detection.yolo_detector import HaarCascadeDetector

        mock_cascade.return_value = Mock()
        detector = HaarCascadeDetector()

        self.assertIsNotNone(detector)
        self.assertIsNotNone(detector.face_cascade)

    def test_haar_detector_detect_faces(self):
        """Test Haar cascade face detection"""
        from src.face_detection.yolo_detector import HaarCascadeDetector

        # Mock the cascade classifier
        with patch('cv2.CascadeClassifier') as mock_cascade_class:
            mock_cascade = Mock()
            mock_cascade.detectMultiScale.return_value = np.array([[100, 100, 50, 50]])
            mock_cascade_class.return_value = mock_cascade

            detector = HaarCascadeDetector()
            faces = detector.detect_faces(self.test_image)

            self.assertIsInstance(faces, list)
            self.assertEqual(len(faces), 1)
            self.assertEqual(len(faces[0]), 4)  # (x1, y1, x2, y2)

    @patch('src.face_detection.yolo_detector.YOLO')
    def test_yolo_detector_initialization(self, mock_yolo):
        """Test YOLO detector initialization"""
        from src.face_detection.yolo_detector import YOLOFaceDetector

        mock_yolo.return_value = Mock()
        detector = YOLOFaceDetector()

        self.assertIsNotNone(detector)
        self.assertTrue(detector.model_available)

    def test_yolo_detector_fallback(self):
        """Test YOLO detector fallback to Haar"""
        from src.face_detection.yolo_detector import YOLOFaceDetector

        # Force YOLO to fail
        with patch('src.face_detection.yolo_detector.YOLO', side_effect=ImportError):
            detector = YOLOFaceDetector()

            self.assertFalse(detector.model_available)
            self.assertIsNotNone(detector.fallback_detector)


class TestFaceRecognition(unittest.TestCase):
    """Test face recognition components"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_encoding = np.random.rand(128).astype(np.float32)

    def test_face_matcher_initialization(self):
        """Test FaceMatcher initialization"""
        from src.face_recognition.matcher import FaceMatcher

        matcher = FaceMatcher(tolerance=0.5)
        self.assertIsNotNone(matcher)
        self.assertEqual(matcher.tolerance, 0.5)
        self.assertEqual(len(matcher.known_face_encodings), 0)

    @patch('src.face_recognition.matcher.face_recognition')
    def test_face_recognition_with_library(self, mock_fr):
        """Test face recognition using face_recognition library"""
        from src.face_recognition.matcher import FaceMatcher

        # Mock face_recognition
        mock_fr.face_encodings.return_value = [self.test_encoding]
        mock_fr.face_distance.return_value = np.array([0.3])

        matcher = FaceMatcher()
        matcher.known_face_encodings = [self.test_encoding]
        matcher.known_face_ids = ['TEST001']
        matcher.known_face_names = ['Test User']

        result_id, result_name, confidence = matcher.recognize_face(self.test_encoding)

        self.assertEqual(result_id, 'TEST001')
        self.assertEqual(result_name, 'Test User')
        self.assertGreater(confidence, 0)

    def test_face_recognition_fallback(self):
        """Test face recognition fallback method"""
        from src.face_recognition.matcher import FaceMatcher

        matcher = FaceMatcher()
        # Add a known face
        matcher.known_face_encodings = [self.test_encoding]
        matcher.known_face_ids = ['TEST001']
        matcher.known_face_names = ['Test User']

        # Test with similar encoding
        similar_encoding = self.test_encoding + np.random.normal(0, 0.1, 128).astype(np.float32)
        result_id, result_name, confidence = matcher.recognize_face(similar_encoding)

        # Should work with fallback method
        self.assertIsNotNone(result_id)

    def test_add_known_face(self):
        """Test adding known faces"""
        from src.face_recognition.matcher import FaceMatcher

        matcher = FaceMatcher()

        # Mock face image
        mock_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        with patch.object(matcher, 'extract_face_features', return_value=self.test_encoding):
            success = matcher.add_known_face(mock_image, 'TEST001', 'Test User')

            self.assertTrue(success)
            self.assertEqual(len(matcher.known_face_encodings), 1)
            self.assertEqual(matcher.known_face_ids[0], 'TEST001')
            self.assertEqual(matcher.known_face_names[0], 'Test User')


class TestLivenessDetection(unittest.TestCase):
    """Test liveness detection components"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        self.test_bbox = (100, 100, 200, 200)

    @patch('src.liveness_detection.mediapipe_liveness.mp')
    def test_mediapipe_liveness_initialization(self, mock_mp):
        """Test MediaPipe liveness detector initialization"""
        from src.liveness_detection.mediapipe_liveness import MediaPipeLivenessDetector

        mock_mp.solutions.face_mesh.FaceMesh.return_value = Mock()
        detector = MediaPipeLivenessDetector()

        self.assertIsNotNone(detector)
        self.assertTrue(detector.model_available)

    def test_mediapipe_liveness_fallback(self):
        """Test MediaPipe liveness detector fallback"""
        from src.liveness_detection.mediapipe_liveness import MediaPipeLivenessDetector

        # Force MediaPipe to fail
        with patch('src.liveness_detection.mediapipe_liveness.mp', side_effect=ImportError):
            detector = MediaPipeLivenessDetector()

            self.assertFalse(detector.model_available)

    def test_fallback_liveness_detection(self):
        """Test fallback liveness detection"""
        from src.liveness_detection.mediapipe_liveness import MediaPipeLivenessDetector

        detector = MediaPipeLivenessDetector()
        detector.model_available = False  # Force fallback

        result = detector.detect_liveness(self.test_image, self.test_bbox)

        self.assertIn('is_live', result)
        self.assertIn('liveness_score', result)
        self.assertIn('method', result)
        self.assertEqual(result['method'], 'fallback')


class TestDatasetManager(unittest.TestCase):
    """Test dataset management components"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_student_id = 'TEST001'
        self.test_name = 'Test User'
        self.test_image_bytes = b'fake_image_data'

    def test_add_student(self):
        """Test adding students to dataset"""
        from src.utils.dataset_manager import add_student

        with patch('src.utils.dataset_manager.save_students') as mock_save:
            success, path = add_student(self.test_student_id, self.test_name, self.test_image_bytes)

            self.assertTrue(success)
            self.assertIsNotNone(path)
            mock_save.assert_called_once()

    def test_remove_student(self):
        """Test removing students from dataset"""
        from src.utils.dataset_manager import remove_student

        with patch('src.utils.dataset_manager.load_students', return_value={self.test_student_id: {'name': self.test_name}}):
            with patch('src.utils.dataset_manager.save_students') as mock_save:
                with patch('os.path.isdir', return_value=True):
                    with patch('os.listdir', return_value=['test.jpg']):
                        with patch('os.remove') as mock_remove:
                            with patch('os.rmdir') as mock_rmdir:
                                success, message = remove_student(self.test_student_id)

                                self.assertTrue(success)
                                mock_save.assert_called_once()
                                mock_remove.assert_called_once()
                                mock_rmdir.assert_called_once()

    def test_list_students(self):
        """Test listing students"""
        from src.utils.dataset_manager import list_students

        mock_students = {
            'TEST001': {'name': 'Alice'},
            'TEST002': {'name': 'Bob'}
        }

        with patch('src.utils.dataset_manager.load_students', return_value=mock_students):
            students = list_students()

            self.assertEqual(len(students), 2)
            self.assertEqual(students[0], ('TEST001', 'Alice'))
            self.assertEqual(students[1], ('TEST002', 'Bob'))


class TestConfiguration(unittest.TestCase):
    """Test configuration management"""

    def test_config_initialization(self):
        """Test configuration manager initialization"""
        from src.config import ConfigManager

        config = ConfigManager()

        self.assertIsNotNone(config)
        self.assertIsNotNone(config._config)

    def test_config_get_set(self):
        """Test configuration get/set operations"""
        from src.config import ConfigManager

        config = ConfigManager()

        # Test setting and getting values
        config.set('test.key', 'test_value')
        self.assertEqual(config.get('test.key'), 'test_value')

        # Test default values
        self.assertIsNone(config.get('nonexistent.key'))
        self.assertEqual(config.get('nonexistent.key', 'default'), 'default')

    def test_config_dot_notation(self):
        """Test dot notation for nested config"""
        from src.config import ConfigManager

        config = ConfigManager()

        config.set('camera.resolution.width', 1920)
        self.assertEqual(config.get('camera.resolution.width'), 1920)


if __name__ == '__main__':
    # Set up logging for tests
    import logging
    logging.basicConfig(level=logging.WARNING)

    # Run tests
    unittest.main(verbosity=2)