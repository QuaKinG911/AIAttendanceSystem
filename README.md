# AI Attendance System

A robust, automated attendance tracking system powered by computer vision and face recognition. This application allows educational institutions to streamline attendance taking, manage classes, and provide real-time analytics for students, teachers, and administrators.

## 🚀 Features

*   **Automated Attendance**: Uses face recognition to mark students present automatically.
*   **Liveness Detection**: Anti-spoofing measures to prevent attendance fraud using photos or videos.
*   **Role-Based Access**:
    *   **Admin**: Manage users, classes, system settings, and view global analytics.
    *   **Teacher**: Manage courses, view attendance reports, and manually override records.
    *   **Student**: View personal attendance history and profile.
    *   **Parent**: Monitor their child's attendance.
*   **Class Management**: Schedule classes, manage enrollments, and track session status.
*   **Analytics**: Detailed insights into attendance rates, lateness, and anomalies.
*   **Notifications**: (Optional) Email and SMS alerts for absence or lateness.

## 📋 Prerequisites

*   **Python 3.10+**
*   **CMake** (Required for compiling `dlib`/`face_recognition`)
*   **Webcam** (For attendance capturing)

## 🛠️ Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/QuaKinG911/AIAttendanceSystem.git
    cd ai-attendance-system
    ```

2.  **Set up a virtual environment**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install system dependencies** (Linux)
    ```bash
    sudo apt-get update
    sudo apt-get install -y python3-dev cmake libopenblas-dev liblapack-dev \
        libx11-dev libgtk-3-dev python3-tk
    ```

4.  **Install Python dependencies**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Download Face Detection Model**
    ```bash
    mkdir -p models
    wget -O models/yolov8x-face-lindevs.pt \
        https://github.com/lindevs/yolov8-face/releases/download/v0.0.0/yolov8x-face-lindevs.pt
    ```

## ⚙️ Configuration

The system uses a centralized configuration system. You can modify settings in `config/settings.json` or use environment variables.

**Key Environment Variables:**
*   `ATTENDANCE_CAMERA_SOURCE`: Camera index (default: `0`)
*   `ATTENDANCE_DATABASE_URL`: Database connection string (default: `sqlite:///data/attendance.db`)
*   `ATTENDANCE_CONFIDENCE_THRESHOLD`: Face recognition confidence threshold (default: `0.7`)

## 🏃‍♂️ Usage

### 1. Start the Application
Run the Flask server:
```bash
python app.py
```
The application will be available at `http://localhost:5000`.

### 2. Default Login Credentials
On the first run, the system creates default users:

| Role | Username | Password |
|------|----------|----------|
| **Admin** | `admin` | `admin456` |
| **Teacher** | `teacher` | `teacher123` |
| **Student** | `student` | `student123` |

### 3. Face Registration

#### Option A: Interactive Capture (Recommended)
Use the interactive tool to capture photos from your webcam:
```bash
python register_student.py
```
Follow the on-screen prompts to enter student details and capture their face.

#### Option B: Manual Setup
1.  Create a directory for the student in `data/faces/`:
    ```bash
    mkdir -p data/faces/<username>
    ```
    *Note: The `<username>` must match an existing user in the database.*

2.  Add clear photos of the student's face to that directory (JPG/PNG).

3.  Run the training script:
    ```bash
    python train_faces.py
    ```

### 4. Taking Attendance
1.  Log in as a **Teacher** or **Admin**.
2.  Navigate to the **Attendance** section.
3.  Select an active class session.
4.  The camera feed will open. Students standing in front of the camera will be marked as "Present" automatically.

## 📂 Project Structure

*   `app.py`: Main entry point for the Flask application.
*   `src/`: Source code directory.
    *   `models.py`: Database models (User, Class, Attendance, etc.).
    *   `config.py`: Configuration management.
    *   `face_recognition/`: Core face detection and recognition logic.
    *   `web/`: Flask blueprints for web routes.
*   `data/`: Stores the SQLite database (`attendance.db`), face images, and encodings.
*   `templates/`: HTML templates for the web interface.
*   `static/`: CSS, JavaScript, and static assets.
*   `train_faces.py`: Script to process images and train the face recognition model.

## 🧪 Development

*   **Run Tests**: `make test`
*   **Lint Code**: `make lint`
*   **Format Code**: `make format`
