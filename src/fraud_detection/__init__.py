# src/fraud_detection/__init__.py - Fraud detection system

import cv2
import numpy as np
from typing import Dict, Any
import logging

class FraudDetector:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def detect_deepfake(self, face_image: np.ndarray) -> Dict[str, Any]:
        """
        Basic deepfake detection using image analysis
        In production, this would use a trained ML model
        """
        try:
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)

            # Simple heuristics (replace with actual model)
            variance = np.var(gray)
            mean_intensity = np.mean(gray)

            # Suspicious if too uniform (potential photo) or too variable
            is_suspicious = variance < 100 or variance > 10000

            return {
                'is_deepfake': is_suspicious,
                'confidence': 0.8 if is_suspicious else 0.2,
                'method': 'basic_heuristic',
                'variance': float(variance),
                'mean_intensity': float(mean_intensity)
            }

        except Exception as e:
            self.logger.error(f"Deepfake detection failed: {e}")
            return {
                'is_deepfake': False,
                'confidence': 0.0,
                'error': str(e)
            }

    def detect_spoofing(self, face_image: np.ndarray, liveness_score: float) -> Dict[str, Any]:
        """
        Detect photo/video spoofing attacks
        """
        try:
            # Edge detection for texture analysis
            edges = cv2.Canny(face_image, 100, 200)
            edge_density = np.sum(edges > 0) / edges.size

            # Color analysis
            hsv = cv2.cvtColor(face_image, cv2.COLOR_BGR2HSV)
            color_variance = np.var(hsv[:, :, 0])  # Hue variance

            # Combine with liveness score
            spoof_score = 1.0 - liveness_score

            # Heuristics
            is_spoof = (
                spoof_score > 0.7 or
                edge_density < 0.05 or  # Too few edges (printed photo)
                color_variance < 50     # Too uniform color (screen capture)
            )

            return {
                'is_spoof': is_spoof,
                'spoof_score': float(spoof_score),
                'edge_density': float(edge_density),
                'color_variance': float(color_variance),
                'confidence': min(0.9, spoof_score + (1 - edge_density) * 0.3)
            }

        except Exception as e:
            self.logger.error(f"Spoofing detection failed: {e}")
            return {
                'is_spoof': False,
                'spoof_score': 0.0,
                'error': str(e)
            }

    def analyze_pattern(self, attendance_records: list) -> Dict[str, Any]:
        """
        Analyze attendance patterns for anomalies
        """
        if len(attendance_records) < 5:
            return {'anomalous': False, 'reason': 'insufficient_data'}

        # Check for suspicious timing patterns
        timestamps = [r['detected_at'] for r in attendance_records if r.get('detected_at')]

        if len(timestamps) < 3:
            return {'anomalous': False, 'reason': 'insufficient_timestamps'}

        # Check if all detections are at exact same time (bulk entry)
        unique_times = len(set(str(t)[:16] for t in timestamps))  # Minute precision
        if unique_times == 1 and len(timestamps) > 2:
            return {
                'anomalous': True,
                'reason': 'bulk_entry_suspicious',
                'confidence': 0.8
            }

        # Check for perfect attendance with high confidence (potential cheating)
        perfect_attendance = all(r.get('status') == 'present' for r in attendance_records)
        high_confidence = all(r.get('confidence', 0) > 0.95 for r in attendance_records)

        if perfect_attendance and high_confidence and len(attendance_records) > 10:
            return {
                'anomalous': True,
                'reason': 'suspiciously_perfect_attendance',
                'confidence': 0.6
            }

        return {'anomalous': False, 'reason': 'normal_pattern'}

# Global instance
fraud_detector = FraudDetector()