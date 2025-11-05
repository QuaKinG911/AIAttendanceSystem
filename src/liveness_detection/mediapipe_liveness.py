import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict
import logging
import time

class MediaPipeLivenessDetector:
    def __init__(self, min_detection_confidence: float = 0.5, min_tracking_confidence: float = 0.5):
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.face_mesh = None
        self.model_available = False
        
        try:
            import mediapipe as mp
            self.mp_face_mesh = mp.solutions.face_mesh
            self.mp_drawing = mp.solutions.drawing_utils
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence,
                max_num_faces=5
            )
            self.model_available = True
            logging.info("MediaPipe Liveness Detector initialized")
        except ImportError:
            logging.warning("MediaPipe not available. Using fallback liveness detection.")
            self.model_available = False
    
    def detect_liveness(self, face_image: np.ndarray, face_bbox: Tuple[int, int, int, int]) -> Dict:
        """
        Detect liveness using various methods
        Returns: Dict with liveness scores and analysis
        """
        if self.model_available:
            return self._mediapipe_liveness_detection(face_image, face_bbox)
        else:
            return self._fallback_liveness_detection(face_image, face_bbox)
    
    def _mediapipe_liveness_detection(self, face_image: np.ndarray, face_bbox: Tuple[int, int, int, int]) -> Dict:
        """Liveness detection using MediaPipe face mesh"""
        try:
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            
            # Process with MediaPipe
            results = self.face_mesh.process(rgb_image)
            
            liveness_score = 0.0
            analysis = {
                'blink_detected': False,
                'eye_aspect_ratio': 0.0,
                'mouth_movement': False,
                'head_pose': None,
                'landmarks_detected': False
            }
            
            if results.multi_face_landmarks:
                analysis['landmarks_detected'] = True
                landmarks = results.multi_face_landmarks[0]
                
                # Calculate eye aspect ratio for blink detection
                left_eye_aspect_ratio = self._calculate_eye_aspect_ratio(landmarks, 'left')
                right_eye_aspect_ratio = self._calculate_eye_aspect_ratio(landmarks, 'right')
                avg_eye_aspect_ratio = (left_eye_aspect_ratio + right_eye_aspect_ratio) / 2
                
                analysis['eye_aspect_ratio'] = avg_eye_aspect_ratio
                
                # Simple blink detection (low eye aspect ratio)
                if avg_eye_aspect_ratio < 0.2:
                    analysis['blink_detected'] = True
                    liveness_score += 0.3
                
                # Check for mouth movement
                mouth_aspect_ratio = self._calculate_mouth_aspect_ratio(landmarks)
                if mouth_aspect_ratio > 0.5:
                    analysis['mouth_movement'] = True
                    liveness_score += 0.2
                
                # Head pose estimation (simplified)
                head_pose = self._estimate_head_pose(landmarks)
                analysis['head_pose'] = head_pose
                
                # Check if face is in reasonable orientation
                if abs(head_pose['pitch']) < 30 and abs(head_pose['yaw']) < 30:
                    liveness_score += 0.3
                
                # Bonus for having good landmark detection
                liveness_score += 0.2
                
            else:
                # No landmarks detected
                liveness_score = 0.0
            
            # Normalize score
            liveness_score = min(liveness_score, 1.0)
            
            return {
                'is_live': liveness_score > 0.4,  # Lowered threshold for testing
                'liveness_score': liveness_score,
                'analysis': analysis,
                'method': 'mediapipe'
            }
            
        except Exception as e:
            logging.error(f"Error in MediaPipe liveness detection: {e}")
            return self._fallback_liveness_detection(face_image, face_bbox)
    
    def _fallback_liveness_detection(self, face_image: np.ndarray, face_bbox: Tuple[int, int, int, int]) -> Dict:
        """Fallback liveness detection using basic computer vision"""
        try:
            x1, y1, x2, y2 = face_bbox
            face_roi = face_image[y1:y2, x1:x2]
            
            if face_roi.size == 0:
                return {
                    'is_live': False,
                    'liveness_score': 0.0,
                    'analysis': {'error': 'Invalid face region'},
                    'method': 'fallback'
                }
            
            # Convert to grayscale
            gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            
            # Calculate basic metrics
            liveness_score = 0.0
            analysis = {}
            
            # Edge detection - real faces have more edges than photos
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            analysis['edge_density'] = edge_density
            
            if edge_density > 0.05:  # Threshold for edge density
                liveness_score += 0.3
            
            # Texture analysis using Laplacian variance
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            analysis['texture_variance'] = laplacian_var
            
            if laplacian_var > 100:  # Threshold for texture
                liveness_score += 0.3
            
            # Color variation analysis
            hsv = cv2.cvtColor(face_roi, cv2.COLOR_BGR2HSV)
            saturation_std = np.std(hsv[:, :, 1])
            analysis['saturation_variation'] = saturation_std
            
            if saturation_std > 20:  # Threshold for color variation
                liveness_score += 0.2
            
            # Basic face quality check
            face_area = (x2 - x1) * (y2 - y1)
            image_area = face_image.shape[0] * face_image.shape[1]
            face_ratio = face_area / image_area
            
            if 0.01 < face_ratio < 0.5:  # Reasonable face size
                liveness_score += 0.2
            
            # Normalize score
            liveness_score = min(liveness_score, 1.0)
            
            return {
                'is_live': liveness_score > 0.5,
                'liveness_score': liveness_score,
                'analysis': analysis,
                'method': 'fallback'
            }
            
        except Exception as e:
            logging.error(f"Error in fallback liveness detection: {e}")
            return {
                'is_live': False,
                'liveness_score': 0.0,
                'analysis': {'error': str(e)},
                'method': 'fallback_error'
            }
    
    def _calculate_eye_aspect_ratio(self, landmarks, eye_side: str) -> float:
        """Calculate eye aspect ratio for blink detection"""
        try:
            # Eye landmark indices (simplified for MediaPipe)
            if eye_side == 'left':
                eye_indices = [33, 7, 163, 144]  # Left eye landmarks
            else:
                eye_indices = [362, 398, 384, 385]  # Right eye landmarks
            
            # Get eye landmark coordinates
            eye_points = []
            for idx in eye_indices:
                if idx < len(landmarks.landmark):
                    point = landmarks.landmark[idx]
                    eye_points.append([point.x, point.y])
            
            if len(eye_points) == 4:
                # Calculate eye aspect ratio
                A = np.linalg.norm(np.array(eye_points[1]) - np.array(eye_points[2]))
                B = np.linalg.norm(np.array(eye_points[0]) - np.array(eye_points[3]))
                C = np.linalg.norm(np.array(eye_points[0]) - np.array(eye_points[1]))
                
                ear = (A + B) / (2.0 * C) if C > 0 else 0.0
                return float(ear)
            
            return 0.0
            
        except Exception as e:
            logging.error(f"Error calculating eye aspect ratio: {e}")
            return 0.0
    
    def _calculate_mouth_aspect_ratio(self, landmarks) -> float:
        """Calculate mouth aspect ratio for mouth movement detection"""
        try:
            # Mouth landmark indices (simplified)
            mouth_indices = [13, 14, 78, 80]  # Upper and lower lip landmarks
            
            mouth_points = []
            for idx in mouth_indices:
                if idx < len(landmarks.landmark):
                    point = landmarks.landmark[idx]
                    mouth_points.append([point.x, point.y])
            
            if len(mouth_points) == 4:
                # Calculate mouth aspect ratio
                A = np.linalg.norm(np.array(mouth_points[1]) - np.array(mouth_points[2]))
                B = np.linalg.norm(np.array(mouth_points[0]) - np.array(mouth_points[3]))
                
                mar = A / B if B > 0 else 0.0
                return float(mar)
            
            return 0.0
            
        except Exception as e:
            logging.error(f"Error calculating mouth aspect ratio: {e}")
            return 0.0
    
    def _estimate_head_pose(self, landmarks) -> Dict:
        """Estimate head pose from face landmarks"""
        try:
            # Simplified head pose estimation
            # Use nose tip and other facial landmarks to estimate orientation
            
            nose_tip = landmarks.landmark[1]  # Nose tip
            chin = landmarks.landmark[175]    # Chin
            left_eye = landmarks.landmark[33]  # Left eye corner
            right_eye = landmarks.landmark[362]  # Right eye corner
            
            # Calculate pitch (up/down tilt)
            pitch = np.arctan2(nose_tip.y - chin.y, abs(nose_tip.z - chin.z)) * 180 / np.pi
            
            # Calculate yaw (left/right turn)
            yaw = np.arctan2(left_eye.x - right_eye.x, abs(left_eye.z - right_eye.z)) * 180 / np.pi
            
            # Calculate roll (head tilt)
            roll = np.arctan2(left_eye.y - right_eye.y, abs(left_eye.x - right_eye.x)) * 180 / np.pi
            
            return {
                'pitch': float(pitch),
                'yaw': float(yaw),
                'roll': float(roll)
            }
            
        except Exception as e:
            logging.error(f"Error estimating head pose: {e}")
            return {'pitch': 0.0, 'yaw': 0.0, 'roll': 0.0}
    
    def draw_liveness_info(self, image: np.ndarray, face_bbox: Tuple[int, int, int, int], 
                          liveness_result: Dict) -> np.ndarray:
        """Draw liveness detection results on image"""
        result_image = image.copy()
        x1, y1, x2, y2 = face_bbox
        
        # Color based on liveness result
        color = (0, 255, 0) if liveness_result['is_live'] else (0, 0, 255)
        
        # Draw bounding box
        cv2.rectangle(result_image, (x1, y1), (x2, y2), color, 2)
        
        # Draw liveness score
        score_text = f"Liveness: {liveness_result['liveness_score']:.2f}"
        cv2.putText(result_image, score_text, (x1, y1 - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Draw method used
        method_text = f"Method: {liveness_result['method']}"
        cv2.putText(result_image, method_text, (x1, y1 - 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        return result_image