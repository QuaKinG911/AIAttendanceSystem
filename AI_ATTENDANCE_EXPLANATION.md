# AI Attendance System: Technical Overview

This document provides a detailed explanation of how the AI Attendance System works, covering the entire pipeline from face detection to database recording.

## 1. System Architecture

The system is built using a modular architecture with the following key components:

*   **Camera Pipeline (`src/camera_pipeline`)**: Orchestrates the video capture and processing flow.
*   **Face Detection (`src/face_detection`)**: Locates faces within video frames.
*   **Face Recognition (`src/face_recognition`)**: Identifies the detected faces by comparing them against a known database.
*   **Database Models (`src/models.py`)**: Stores user data, class schedules, and attendance records.
*   **API Layer (`src/api`)**: Exposes endpoints for the web interface to interact with the system.

## 2. The Attendance Process Flow

The core attendance process runs in a continuous loop within `AttendanceSystem.run()`:

1.  **Frame Capture**: The system captures a video frame from the configured camera source.
2.  **Face Detection**: The frame is passed to the `YOLOFaceDetector`.
3.  **Face Recognition**: Detected face regions are extracted and sent to the `FaceMatcher`.
4.  **Matching & Validation**: The system attempts to match the face against known students.
5.  **Recording**: If a match is found and meets confidence thresholds, attendance is recorded in the database.

## 3. Detailed Component Analysis

### A. Face Detection (`src/face_detection/yolo_detector.py`)
*   **Technology**: Uses a YOLO (You Only Look Once) based model for real-time object detection.
*   **Function**: Scans the entire image frame to find bounding boxes of faces.
*   **Output**: Returns coordinates `(x1, y1, x2, y2)` and a detection confidence score for each face found.

### B. Face Recognition (`src/face_recognition/matcher.py`)
This is the brain of the system. It handles the identification of students.

1.  **Quality Validation**: Before attempting recognition, the system validates the face image quality:
    *   **Brightness**: Checks if the image is too dark or too bright.
    *   **Focus**: Uses Laplacian variance to ensure the image isn't blurry.
    *   **Angle/Pose**: Checks if the face is looking straight at the camera.
    *   **Size**: Ensures the face is large enough (min 64x64 pixels) for accurate recognition.

2.  **Feature Extraction**:
    *   **Primary Method**: Uses the `face_recognition` library (based on dlib's state-of-the-art ResNet model) to generate a 128-dimensional vector (encoding) that uniquely represents the face.
    *   **Fallback**: If the library fails, it falls back to a simple feature extraction method (histogram equalization + normalization), though this is less accurate.

3.  **Matching Logic**:
    *   **Distance Calculation**: Calculates the Euclidean distance between the live face encoding and all stored student encodings.
    *   **Thresholding**: If the distance is below the `tolerance` (default 0.6), it's considered a match. Lower distance means a better match.
    *   **Confidence Score**: The distance is converted into a confidence score (0.0 to 1.0).

### C. Attendance Recording (`src/camera_pipeline/attendance_system.py`)
Once a face is recognized:

1.  **Session Check**: Verifies that an active attendance session exists (`active_session_id` is set).
2.  **Debouncing**: Prevents spamming the database. It checks `last_process_time` to ensure the same student isn't processed more than once every 5 seconds.
3.  **Duplicate Check**: Checks `processed_students` set to see if the student has already been marked present for *this specific session*.
4.  **Database Commit**: Creates a new `AttendanceRecord` with:
    *   `student_id`: The identified student.
    *   `session_id`: The current class session.
    *   `status`: 'present' (logic for 'late' is handled by comparing timestamps against session windows).
    *   `confidence_score`: The match confidence.
    *   `detected_at`: Current timestamp.

## 4. Data Management

*   **Face Encodings**: Stored in a serialized pickle file (`data/face_encodings/face_database.pkl`) for fast loading during runtime.
*   **Profile Photos**: When a student uploads a photo via the web interface, it is saved to `data/faces/{username}/` (the same directory used by admins) and treated as the primary reference image for face recognition.
*   **Database**: PostgreSQL (via SQLAlchemy) stores the relational data (Users, Classes, Sessions, Records).

## 5. Web Integration

*   **Teacher Dashboard**: Teachers start sessions via the web UI. This triggers the `start_session` API, creating a new `AttendanceSession` record.
*   **Real-time Feedback**: The system can draw bounding boxes and names on the video feed (processed frames) which can be streamed back to the client.
*   **Reporting**: Admins and teachers can view attendance logs, which are simply queries against the `AttendanceRecord` table.
