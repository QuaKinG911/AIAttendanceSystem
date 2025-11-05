import cv2
import numpy as np
import pickle
import os
from typing import List, Tuple, Optional, Dict
import logging
from sklearn.metrics.pairwise import cosine_similarity

class FaceMatcher:
    def __init__(self, tolerance: float = 0.4):  # Lower tolerance for better recognition
        self.tolerance = tolerance
        self.known_face_encodings = []
        self.known_face_ids = []
        self.known_face_names = []
        logging.info(f"Face Matcher initialized with tolerance: {tolerance}")
    
    def load_known_faces(self, database_path: str):
        """Load known face encodings from database"""
        try:
            if os.path.exists(database_path):
                with open(database_path, 'rb') as f:
                    data = pickle.load(f)
                    self.known_face_encodings = data.get('encodings', [])
                    self.known_face_ids = data.get('ids', [])
                    self.known_face_names = data.get('names', [])
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
                'names': self.known_face_names
            }
            with open(database_path, 'wb') as f:
                pickle.dump(data, f)
            logging.info(f"Saved {len(self.known_face_encodings)} known faces")
        except Exception as e:
            logging.error(f"Error saving face database: {e}")
    
    def extract_face_features(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """Extract face features from face image"""
        try:
            # Try to use face_recognition library if available
            try:
                import face_recognition

                # Convert BGR to RGB
                rgb_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)

                # Extract face encoding
                face_encodings = face_recognition.face_encodings(rgb_image)

                if len(face_encodings) > 0:
                    return face_encodings[0]
                else:
                    logging.warning("No face encoding found in the image - skipping recognition")
                    return None
            except ImportError:
                logging.warning("face_recognition library not available. Using simple features.")
                return self._extract_simple_features(face_image)

        except Exception as e:
            logging.error(f"Error extracting face features: {e}")
            return None
    
    def _extract_simple_features(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """Simple feature extraction as fallback"""
        try:
            # Resize to standard size
            resized = cv2.resize(face_image, (64, 64))
            
            # Convert to grayscale
            gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
            
            # Apply histogram equalization
            equalized = cv2.equalizeHist(gray)
            
            # Normalize
            normalized = equalized / 255.0
            
            # Flatten to create feature vector
            features = normalized.flatten()
            
            return features
        except Exception as e:
            logging.error(f"Error extracting simple features: {e}")
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
            # Try to use face_recognition library if available
            try:
                import face_recognition
                
                # Calculate distances
                distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                
                # Find best match
                best_match_index = np.argmin(distances)
                min_distance = distances[best_match_index]
                
                # Convert distance to confidence (lower distance = higher confidence)
                confidence = 1.0 - min_distance

                # Debug logging
                logging.debug(f"Face recognition: min_distance={min_distance:.3f}, tolerance={self.tolerance}, confidence={confidence:.3f}")

                if min_distance <= self.tolerance:
                    student_id = self.known_face_ids[best_match_index]
                    student_name = self.known_face_names[best_match_index]
                    logging.info(f"Face recognized: {student_name} ({student_id}) with confidence {confidence:.3f}")
                    return student_id, student_name, confidence
                else:
                    logging.debug(f"Face not recognized: distance {min_distance:.3f} > tolerance {self.tolerance}")
                    return None, None, confidence
                    
            except ImportError:
                # Fallback: use cosine similarity
                similarities = []
                for known_encoding in self.known_face_encodings:
                    if len(face_encoding) == len(known_encoding):
                        similarity = cosine_similarity([face_encoding], [known_encoding])[0][0]
                        similarities.append(float(similarity))
                    else:
                        similarities.append(0.0)
                
                if similarities:
                    best_match_index = np.argmax(similarities)
                    max_similarity = similarities[best_match_index]
                    
                    if max_similarity >= 0.7:  # Higher threshold for simple features
                        student_id = self.known_face_ids[best_match_index]
                        student_name = self.known_face_names[best_match_index]
                        return student_id, student_name, max_similarity
                    else:
                        return None, None, max_similarity
                else:
                    return None, None, 0.0
                    
        except Exception as e:
            logging.error(f"Error recognizing face: {e}")
            return None, None, 0.0
    
    def add_known_face(self, face_image: np.ndarray, student_id: str, student_name: str):
        """Add a new known face to the database"""
        face_encoding = self.extract_face_features(face_image)
        if face_encoding is not None:
            self.known_face_encodings.append(face_encoding)
            self.known_face_ids.append(student_id)
            self.known_face_names.append(student_name)
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