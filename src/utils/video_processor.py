"""
Video processor for face enrollment.
Extracts frames from video and detects faces for training.
"""
import cv2
import os
import tempfile
from typing import Tuple, List
import logging

class VideoProcessor:
    def __init__(self, frame_skip=6):
        """
        Initialize video processor.
        
        Args:
            frame_skip: Extract every Nth frame (default 6 = 5 FPS from 30 FPS video)
        """
        self.frame_skip = frame_skip
        
    def process_enrollment_video(self, video_path: str, student_id: str, output_dir: str) -> Tuple[bool, str, int]:
        """
        Process enrollment video and extract face frames.
        
        Args:
            video_path: Path to video file
            student_id: Student ID
            output_dir: Directory to save extracted frames
            
        Returns:
            (success, message, frames_extracted)
        """
        try:
            # Open video
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return False, "Failed to open video file", 0
            
            # Create output directory
            student_dir = os.path.join(output_dir, student_id)
            os.makedirs(student_dir, exist_ok=True)
            
            # Load face detector
            from src.face_detection.yolo_detector import YOLOFaceDetector
            detector = YOLOFaceDetector()
            
            frame_count = 0
            saved_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Skip frames
                if frame_count % self.frame_skip != 0:
                    frame_count += 1
                    continue
                
                # Detect faces
                faces = detector.detect_faces(frame)
                
                # Save the largest face (assume it's the enrollment subject)
                if faces:
                    largest_face = max(faces, key=lambda f: (f[2]-f[0]) * (f[3]-f[1]))
                    x1, y1, x2, y2 = largest_face
                    
                    # Crop face with some padding
                    padding = 20
                    h, w = frame.shape[:2]
                    x1 = max(0, x1 - padding)
                    y1 = max(0, y1 - padding)
                    x2 = min(w, x2 + padding)
                    y2 = min(h, y2 + padding)
                    
                    face_img = frame[y1:y2, x1:x2]
                    
                    # Save frame
                    output_path = os.path.join(student_dir, f'{student_id}_{saved_count + 1}.jpg')
                    cv2.imwrite(output_path, face_img)
                    saved_count += 1
                
                frame_count += 1
            
            cap.release()
            
            if saved_count == 0:
                return False, "No faces detected in video", 0
            
            logging.info(f"Extracted {saved_count} frames from video for student {student_id}")
            return True, f"Successfully extracted {saved_count} frames", saved_count
            
        except Exception as e:
            logging.error(f"Error processing video: {e}")
            return False, f"Error: {str(e)}", 0
    
    def cleanup_temp_file(self, file_path: str):
        """Remove temporary video file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logging.warning(f"Failed to cleanup temp file: {e}")
