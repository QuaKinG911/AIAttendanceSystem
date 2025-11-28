import cv2
import numpy as np
import pickle
import os
from typing import List, Tuple, Optional, Dict, Any
import logging
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path
import face_recognition
try:
    FACE_RECOGNITION_AVAILABLE = True
    logging.info("face_recognition library loaded successfully")
except ImportError:
    face_recognition = None
    FACE_RECOGNITION_AVAILABLE = False
    logging.warning("face_recognition not available. Using basic features only.")

class FaceMatcher:
    def __init__(self, tolerance: float = 0.4, confidence_threshold: float = 0.6):
        self.tolerance = tolerance
        self.confidence_threshold = confidence_threshold
        self.known_face_encodings = []
        self.known_face_ids = []
        self.known_face_names = []
        self.known_face_metadata = []  # Store additional metadata

        logging.info(f"Face Matcher initialized with tolerance: {tolerance}, confidence_threshold: {confidence_threshold}")

    def validate_face_quality(self, face_image: np.ndarray) -> Dict[str, Any]:
        """Validate face image quality for recognition"""
        quality_metrics = {
            'brightness': self._check_brightness(face_image),
            'focus': self._check_focus(face_image),
            'angle': self._check_face_angle(face_image),
            'size': self._check_face_size(face_image),
            'pose': self._check_face_pose(face_image),
            'overall_score': 0.0
        }

        # Calculate overall quality score (0-1, higher is better)
        quality_metrics['overall_score'] = (
            quality_metrics['brightness'] * 0.2 +
            quality_metrics['focus'] * 0.2 +
            quality_metrics['angle'] * 0.15 +
            quality_metrics['size'] * 0.15 +
            quality_metrics['pose'] * 0.3
        )

        return quality_metrics

    def _check_brightness(self, image: np.ndarray) -> float:
        """Check image brightness (0-1, higher is better)"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray) / 255.0

            # Optimal brightness is around 0.4-0.7
            if 0.3 <= brightness <= 0.8:
                return 1.0
            elif brightness < 0.2 or brightness > 0.9:
                return 0.2
            else:
                return 0.7
        except:
            return 0.5

    def _check_focus(self, image: np.ndarray) -> float:
        """Check image focus using Laplacian variance (0-1, higher is better)"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

            # Normalize focus score (higher variance = sharper image)
            focus_score = min(1.0, laplacian_var / 500.0)
            return focus_score
        except:
            return 0.5

    def _check_face_angle(self, face_image: np.ndarray) -> float:
        """Check face angle using basic heuristics (0-1, higher is better)"""
        try:
            # Simple check: if face is too skewed, it might be at an angle
            height, width = face_image.shape[:2]

            # Check aspect ratio (faces should be roughly square)
            aspect_ratio = width / height
            if 0.7 <= aspect_ratio <= 1.4:
                return 1.0
            else:
                return 0.5
        except:
            return 0.5

    def _check_face_size(self, face_image: np.ndarray) -> float:
        """Check if face is large enough for recognition (0-1, higher is better)"""
        try:
            height, width = face_image.shape[:2]
            min_dimension = min(height, width)

            # Faces should be at least 64x64 pixels for good recognition
            if min_dimension >= 100:
                return 1.0
            elif min_dimension >= 64:
                return 0.7
            else:
                return 0.3
        except:
            return 0.5

    def _check_face_pose(self, face_image: np.ndarray) -> float:
        """Check face pose using facial landmarks (0-1, higher is better)"""
        try:
            if not FACE_RECOGNITION_AVAILABLE:
                return 0.5  # Neutral score if landmarks not available

            # Convert to RGB for face_recognition
            rgb_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)

            # Get face landmarks
            try:
                face_landmarks_list = face_recognition.face_landmarks(rgb_image)  # type: ignore
            except AttributeError:
                return 0.5  # Fallback if landmarks not available

            if not face_landmarks_list:
                return 0.3  # No face detected

            landmarks = face_landmarks_list[0]

            # Calculate pose estimation using eye and nose positions
            left_eye = np.mean(landmarks['left_eye'], axis=0)
            right_eye = np.mean(landmarks['right_eye'], axis=0)
            nose = np.mean(landmarks['nose_bridge'], axis=0)

            # Calculate eye line angle
            eye_vector = right_eye - left_eye
            eye_angle = np.arctan2(eye_vector[1], eye_vector[0]) * 180 / np.pi

            # Calculate nose position relative to eyes
            eye_center = (left_eye + right_eye) / 2
            nose_offset = nose - eye_center

            # Ideal pose: eyes horizontal, nose centered
            angle_score = max(0.0, 1.0 - abs(eye_angle) / 30.0)  # Within 30 degrees
            center_score = max(0.0, 1.0 - abs(nose_offset[0]) / 20.0)  # Within 20 pixels

            pose_score = (angle_score + center_score) / 2.0
            return pose_score

        except Exception as e:
            logging.error(f"Error checking face pose: {e}")
            return 0.5

    def load_known_faces(self, database_path: str):
        """Load known face encodings from database"""
        try:
            if os.path.exists(database_path):
                with open(database_path, 'rb') as f:
                    data = pickle.load(f)
                    self.known_face_encodings = data.get('encodings', [])
                    self.known_face_ids = data.get('ids', [])
                    self.known_face_names = data.get('names', [])
                    self.known_face_metadata = data.get('metadata', [])
                logging.info(f"Loaded {len(self.known_face_encodings)} known faces")
            else:
                logging.warning(f"Database file not found: {database_path}")
        except Exception as e:
            logging.error(f"Error loading face database: {e}")
    
    def save_known_faces(self, database_path: str):
        """Save known face encodings to database"""
        try:
            os.makedirs(os.path.dirname(database_path), exist_ok=True)
            data = {
                'encodings': self.known_face_encodings,
                'ids': self.known_face_ids,
                'names': self.known_face_names,
                'metadata': self.known_face_metadata
            }
            with open(database_path, 'wb') as f:
                pickle.dump(data, f)
            logging.info(f"Saved {len(self.known_face_encodings)} known faces")
        except Exception as e:
            logging.error(f"Error saving face database: {e}")
    
    def extract_face_features(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """Extract face features from face image"""
        try:
            # Validate face quality first (only if face_recognition is available)
            if FACE_RECOGNITION_AVAILABLE and face_recognition is not None:
                quality = self.validate_face_quality(face_image)
                if quality['overall_score'] < 0.1:  # Lower threshold
                    logging.warning(f"Poor face quality detected: {quality}")
                    return None
                
                # Use face_recognition library if available (128-d vector)
                # Convert BGR to RGB
                rgb_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
                encodings = face_recognition.face_encodings(rgb_image)
                if encodings:
                    return encodings[0]

            # Fallback to simple features (ResNet18)
            logging.debug("Using simple feature extraction (ResNet18)")
            return self._extract_simple_features(face_image)

        except Exception as e:
            logging.error(f"Error extracting face features: {e}")
            return None

    def _extract_simple_features(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """Extract features using HOG (Histogram of Oriented Gradients)"""
        try:
            # Resize to fixed size (64x128 is standard for HOG)
            resized = cv2.resize(face_image, (64, 128))
            
            # Initialize HOG descriptor
            hog = cv2.HOGDescriptor()
            
            # Compute HOG features
            features = hog.compute(resized)
            
            # Flatten to 1D array
            features = features.flatten().astype(np.float32)
            
            # Normalize
            if np.std(features) > 0:
                features = (features - np.mean(features)) / np.std(features)
            
            return features

        except Exception as e:
            logging.error(f"Error extracting HOG features: {e}")
            return None
    
    def recognize_face(self, face_encoding: np.ndarray) -> Tuple[Optional[str], Optional[str], float]:
        """
        Recognize face from encoding
        Returns: (student_id, student_name, confidence)
        """
        if face_encoding is None:
            return None, None, 0.0

        if len(self.known_face_encodings) == 0:
            return None, None, 0.0

        try:
            # Check encoding type based on dimension
            is_dlib_encoding = len(face_encoding) == 128
            
            similarities = []
            for i, known_encoding in enumerate(self.known_face_encodings):
                # Only compare encodings of the same dimension
                if len(face_encoding) == len(known_encoding):
                    if is_dlib_encoding:
                        # For dlib (128-d), use Euclidean distance (lower is better)
                        # We convert it to a similarity score (0-1)
                        distance = np.linalg.norm(face_encoding - known_encoding)
                        # Typical threshold is 0.6. Convert to similarity: 1 - (dist/threshold) or similar
                        # Let's use a simple inversion: 1 / (1 + distance)
                        # Distance 0 -> Sim 1.0
                        # Distance 0.6 -> Sim 0.625
                        similarity = 1.0 / (1.0 + distance)
                        similarities.append((i, similarity))
                    else:
                        # For ResNet (512-d), use Cosine Similarity (higher is better)
                        similarity = cosine_similarity([face_encoding], [known_encoding])[0][0]
                        similarities.append((i, similarity))

            if similarities:
                best_match_index, max_similarity = max(similarities, key=lambda x: x[1])

                # Dynamic threshold based on method
                if is_dlib_encoding:
                    # Use configured threshold (converted to similarity if needed)
                    # self.confidence_threshold is likely a similarity score (0.7 default)
                    threshold = self.confidence_threshold
                else:
                    threshold = 0.30  # Lowered for HOG features

                if max_similarity >= threshold:
                    student_id = self.known_face_ids[best_match_index]
                    student_name = self.known_face_names[best_match_index]
                    logging.info(f"Face recognized: {student_name} ({student_id}) with similarity {max_similarity:.3f}")
                    return student_id, student_name, max_similarity
                else:
                    logging.debug(f"Face not recognized: similarity {max_similarity:.3f} < threshold {threshold}")
                    return None, None, max_similarity

            return None, None, 0.0

        except Exception as e:
            logging.error(f"Error recognizing face: {e}")
            return None, None, 0.0
    
    def add_known_face(self, face_image: np.ndarray, student_id: str, student_name: str, metadata: Dict[str, Any] = None):
        """Add a new known face to the database"""
        face_encoding = self.extract_face_features(face_image)
        if face_encoding is not None:
            self.known_face_encodings.append(face_encoding)
            self.known_face_ids.append(student_id)
            self.known_face_names.append(student_name)
            self.known_face_metadata.append(metadata or {})
            logging.info(f"Added new face: {student_name} ({student_id})")
            return True
        else:
            logging.error(f"Failed to extract encoding for {student_name}")
            return False
    
    def batch_recognize_faces(self, face_encodings: List[np.ndarray]) -> List[Tuple[Optional[str], Optional[str], float]]:
        """Recognize multiple faces at once"""
        results = []
        for encoding in face_encodings:
            student_id, student_name, confidence = self.recognize_face(encoding)
            results.append((student_id, student_name, confidence))
        return results
    
    def get_face_similarity(self, encoding1: np.ndarray, encoding2: np.ndarray) -> float:
        """Calculate similarity between two face encodings"""
        try:
            if len(encoding1) != len(encoding2):
                return 0.0
            
            # Use cosine similarity
            similarity = cosine_similarity([encoding1], [encoding2])[0][0]
            return float(similarity)
        except Exception as e:
            logging.error(f"Error calculating face similarity: {e}")
            return 0.0