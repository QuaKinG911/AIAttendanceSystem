import cv2
import numpy as np
import os
from typing import List, Tuple, Optional
import logging

class HaarCascadeDetector:
    def __init__(self, cascade_path: Optional[str] = None, scale_factor: float = 1.1, 
                 min_neighbors: int = 5, min_size: Tuple[int, int] = (30, 30)):
        if cascade_path is None:
            # Try to find the haar cascade file in common locations
            possible_paths = [
                'haarcascade_frontalface_default.xml',
                '/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml',
                '/usr/local/share/opencv4/haarcascades/haarcascade_frontalface_default.xml',
                './models/haarcascade_frontalface_default.xml'
            ]
            
            # Try cv2.data if available
            try:
                cv2_data_path = cv2.__file__.replace('cv2/__init__.py', 'data/haarcascades/haarcascade_frontalface_default.xml')
                if os.path.exists(cv2_data_path):
                    possible_paths.insert(0, cv2_data_path)
            except:
                pass
            
            cascade_path = None
            for path in possible_paths:
                if path and os.path.exists(path):
                    cascade_path = path
                    break
        
        if not cascade_path or not os.path.exists(str(cascade_path)):
            raise FileNotFoundError(f"Haar cascade file not found. Please download haarcascade_frontalface_default.xml")
        
        self.face_cascade = cv2.CascadeClassifier(str(cascade_path))
        self.scale_factor = scale_factor
        self.min_neighbors = min_neighbors
        self.min_size = min_size
        logging.info("Haar Cascade Face Detector initialized")
    
    def detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces using Haar cascades
        Returns: List of bounding boxes [(x, y, w, h), ...]
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=self.scale_factor,
            minNeighbors=self.min_neighbors,
            minSize=self.min_size
        )
        
        # Convert (x, y, w, h) to (x1, y1, x2, y2)
        result = []
        for (x, y, w, h) in faces:
            result.append((x, y, x + w, y + h))
        
        return result
    
    def detect_faces_with_confidence(self, image: np.ndarray) -> List[Tuple[int, int, int, int, float]]:
        """
        Haar cascades don't provide confidence scores, so we use fixed confidence
        Returns: List of [(x1, y1, x2, y2, confidence), ...]
        """
        faces = self.detect_faces(image)
        return [(x1, y1, x2, y2, 0.8) for (x1, y1, x2, y2) in faces]
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better detection"""
        # Apply histogram equalization for better contrast
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        equalized = cv2.equalizeHist(gray)
        return cv2.cvtColor(equalized, cv2.COLOR_GRAY2BGR)
    
    def draw_detections(self, image: np.ndarray, faces: List[Tuple[int, int, int, int]]) -> np.ndarray:
        """Draw bounding boxes on image"""
        result_image = image.copy()
        for (x1, y1, x2, y2) in faces:
            cv2.rectangle(result_image, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.putText(result_image, "Haar Face", (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        return result_image


class YOLOFaceDetector:
    def __init__(self, model_path: str = "models/yolov8x-face-lindevs.pt", confidence_threshold: float = 0.5):
        try:
            from ultralytics import YOLO
            import torch

            # Convert to absolute path if relative
            if not os.path.isabs(model_path):
                # Get the directory of this file and go up to project root
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                model_path = os.path.join(project_root, model_path)

            # Check if model file exists
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"YOLO model not found: {model_path}")

            logging.info(f"Loading YOLO model from: {model_path}")
            self.model = YOLO(model_path)
            self.confidence_threshold = confidence_threshold
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model.to(self.device)
            self.model_available = True
            logging.info(f"YOLO Face Detector initialized on {self.device}")
        except Exception as e:
            logging.warning(f"YOLO initialization failed: {e}. Using fallback detector.")
            self.model_available = False
            self.fallback_detector = HaarCascadeDetector()

    def detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in the input image
        Returns: List of bounding boxes [(x1, y1, x2, y2), ...]
        """
        if not self.model_available:
            return self.fallback_detector.detect_faces(image)
        
        results = self.model(image, conf=self.confidence_threshold)
        faces = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    faces.append((int(x1), int(y1), int(x2), int(y2)))
        
        return faces
    
    def detect_faces_with_confidence(self, image: np.ndarray) -> List[Tuple[int, int, int, int, float]]:
        """
        Detect faces with confidence scores
        Returns: List of [(x1, y1, x2, y2, confidence), ...]
        """
        if not self.model_available:
            logging.debug("Using Haar Cascade fallback for face detection")
            return self.fallback_detector.detect_faces_with_confidence(image)

        try:
            results = self.model(image, conf=self.confidence_threshold, verbose=False)
            faces = []

            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        conf = box.conf[0].cpu().numpy()
                        faces.append((int(x1), int(y1), int(x2), int(y2), float(conf)))

            logging.debug(f"YOLO detected {len(faces)} faces")
            return faces
        except Exception as e:
            logging.warning(f"YOLO detection failed: {e}. Using fallback.")
            return self.fallback_detector.detect_faces_with_confidence(image)
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better detection"""
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image
    
    def draw_detections(self, image: np.ndarray, faces: List[Tuple[int, int, int, int]]) -> np.ndarray:
        """Draw bounding boxes on image"""
        result_image = image.copy()
        for (x1, y1, x2, y2) in faces:
            cv2.rectangle(result_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(result_image, "Face", (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return result_image