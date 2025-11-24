import cv2
import numpy as np
import os
from typing import List, Tuple, Optional
import logging

class YOLOFaceDetector:
    def __init__(self, model_path: Optional[str] = None, confidence_threshold: float = 0.5):
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.model_available = False
        self.fallback_detector = None

        # Try to initialize YOLO model
        if model_path:
            self._init_yolo_model(model_path)

        # If YOLO fails, initialize fallback detector
        if not self.model_available:
            self._init_fallback_detector()

    def _init_yolo_model(self, model_path: str):
        """Initialize YOLO model for face detection"""
        try:
            from ultralytics import YOLO  # type: ignore
            import torch  # type: ignore

            # Convert to absolute path if relative
            if not os.path.isabs(model_path):
                # Get the directory of this file and go up to project root
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                model_path = os.path.join(project_root, model_path)

            # Check if model file exists
            if not os.path.exists(model_path):
                logging.warning(f"YOLO model not found: {model_path}. Using fallback detector.")
                return

            logging.info(f"Loading YOLO model from: {model_path}")
            self.model = YOLO(model_path)
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model.to(self.device)
            self.model_available = True
            logging.info(f"YOLO Face Detector initialized on {self.device}")
        except ImportError:
            logging.warning("ultralytics or torch not available. Using fallback detector.")
            self.model_available = False
        except Exception as e:
            logging.error(f"YOLO initialization failed: {e}. Using fallback detector.")
            self.model_available = False

    def _init_fallback_detector(self):
        """Initialize OpenCV Haar cascade as fallback"""
        try:
            # Try to find Haar cascade file
            possible_paths = [
                '/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml',
                '/usr/local/share/opencv4/haarcascades/haarcascade_frontalface_default.xml',
                cv2.__file__.replace('__init__.py', 'data/haarcascades/haarcascade_frontalface_default.xml') if hasattr(cv2, '__file__') else None
            ]

            cascade_path = None
            for path in possible_paths:
                if path and os.path.exists(path):
                    cascade_path = path
                    break

            if cascade_path:
                self.fallback_detector = cv2.CascadeClassifier(cascade_path)
                logging.info("Initialized OpenCV Haar cascade face detector as fallback")
            else:
                logging.warning("OpenCV Haar cascade not found. Face detection will be limited.")
        except Exception as e:
            logging.error(f"Failed to initialize fallback detector: {e}")

    def detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in the input image
        Returns: List of bounding boxes [(x1, y1, x2, y2), ...]
        """
        # Try YOLO first
        if self.model_available and self.model is not None:
            try:
                results = self.model(image, conf=self.confidence_threshold, verbose=False)
                faces = []

                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            faces.append((int(x1), int(y1), int(x2), int(y2)))

                if faces:
                    return faces
            except Exception as e:
                logging.error(f"YOLO detection failed: {e}")

        # Fallback to Haar cascade
        if self.fallback_detector is not None:
            try:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                faces = self.fallback_detector.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30)
                )

                # Convert to (x1, y1, x2, y2) format
                return [(int(x), int(y), int(x+w), int(y+h)) for (x, y, w, h) in faces]
            except Exception as e:
                logging.error(f"Haar cascade detection failed: {e}")

        logging.warning("No face detection method available")
        return []
    
    def detect_faces_with_confidence(self, image: np.ndarray) -> List[Tuple[int, int, int, int, float]]:
        """
        Detect faces with confidence scores
        Returns: List of [(x1, y1, x2, y2, confidence), ...]
        """
        # Try YOLO first
        if self.model_available and self.model is not None:
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

                if faces:
                    logging.debug(f"YOLO detected {len(faces)} faces")
                    return faces
            except Exception as e:
                logging.error(f"YOLO detection failed: {e}")

        # Fallback to Haar cascade (no confidence scores available)
        if self.fallback_detector is not None:
            try:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                detected_faces = self.fallback_detector.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30)
                )

                # Convert to format with dummy confidence score
                faces = [(int(x), int(y), int(x+w), int(y+h), 0.8) for (x, y, w, h) in detected_faces]
                logging.debug(f"Haar cascade detected {len(faces)} faces")
                return faces
            except Exception as e:
                logging.error(f"Haar cascade detection failed: {e}")

        logging.warning("No face detection method available")
        return []
    
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