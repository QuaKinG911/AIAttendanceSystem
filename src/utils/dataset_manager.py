import os
import json
from typing import Dict, List, Optional, Tuple


import logging

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
# New canonical folder for recognition reference images
DATASET_DIR = os.path.join(PROJECT_ROOT, 'data', 'faces')
STUDENTS_JSON = os.path.join(DATASET_DIR, 'students.json')

logger = logging.getLogger(__name__)


def ensure_dataset_dirs() -> None:
    os.makedirs(DATASET_DIR, exist_ok=True)
    try:
        os.chmod(DATASET_DIR, 0o777)
    except Exception:
        pass
        
    # Migrate from old layout if present: data/students -> data/faces
    old_dir = os.path.join(PROJECT_ROOT, 'data', 'students')
    if os.path.isdir(old_dir):
        try:
            for entry in os.listdir(old_dir):
                src_path = os.path.join(old_dir, entry)
                dst_path = os.path.join(DATASET_DIR, entry)
                if os.path.isdir(src_path) and not os.path.exists(dst_path):
                    try:
                        os.rename(src_path, dst_path)
                    except Exception:
                        pass
        except Exception:
            pass
    if not os.path.exists(STUDENTS_JSON):
        with open(STUDENTS_JSON, 'w') as f:
            json.dump({}, f, indent=2)
        try:
            os.chmod(STUDENTS_JSON, 0o666)
        except Exception:
            pass
    elif os.path.exists(STUDENTS_JSON):
        try:
            os.chmod(STUDENTS_JSON, 0o666)
        except Exception:
            pass


def load_students() -> Dict[str, Dict[str, str]]:
    ensure_dataset_dirs()
    try:
        with open(STUDENTS_JSON, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def save_students(students: Dict[str, Dict[str, str]]) -> None:
    ensure_dataset_dirs()
    with open(STUDENTS_JSON, 'w') as f:
        json.dump(students, f, indent=2)


def get_student_dir(student_id: str) -> str:
    return os.path.join(DATASET_DIR, student_id)


def add_student(student_id: str, name: str, image_bytes: bytes, image_ext: str = '.jpg') -> Tuple[bool, str]:
    """Add or update a student and save their primary image.

    Returns (ok, path_or_error)
    """
    ensure_dataset_dirs()
    if not student_id:
        return False, 'Student ID is required'
    if not name:
        return False, 'Student name is required'

    students = load_students()
    students[student_id] = {'name': name}

    sdir = get_student_dir(student_id)
    os.makedirs(sdir, exist_ok=True)
    img_path = os.path.join(sdir, f'{student_id}{image_ext}')
    try:
        with open(img_path, 'wb') as f:
            f.write(image_bytes)
    except Exception as e:
        return False, f'Failed to save image: {e}'

    save_students(students)
    
    # Trigger training to update encodings
    try:
        # We import here to avoid circular imports if train_faces imports this module
        import sys
        if PROJECT_ROOT not in sys.path:
            sys.path.append(PROJECT_ROOT)
        
        # Use a subprocess to run training to avoid any import/context issues
        import subprocess
        subprocess.Popen([sys.executable, os.path.join(PROJECT_ROOT, 'train_faces.py')])
        
    except Exception as e:
        logger.warning(f"Failed to trigger training: {e}")
        
    return True, img_path


def remove_student(student_id: str) -> Tuple[bool, str]:
    ensure_dataset_dirs()
    students = load_students()
    if student_id not in students:
        return False, 'Student not found'
    try:
        # Remove files in student dir
        sdir = get_student_dir(student_id)
        if os.path.isdir(sdir):
            for name in os.listdir(sdir):
                try:
                    os.remove(os.path.join(sdir, name))
                except Exception:
                    pass
            try:
                os.rmdir(sdir)
            except Exception:
                pass
        students.pop(student_id, None)
        save_students(students)
        return True, 'Removed'
    except Exception as e:
        return False, str(e)


def list_students() -> List[Tuple[str, str]]:
    students = load_students()
    return sorted([(sid, meta.get('name', '')) for sid, meta in students.items()], key=lambda x: x[0])


def save_student_photo(student_id: str, image_bytes: bytes, image_ext: str = '.jpg') -> Tuple[bool, str]:
    """Save a photo for an existing student. Supports multiple photos.

    Returns (ok, path_or_error)
    """
    ensure_dataset_dirs()
    if not student_id:
        return False, 'Student ID is required'

    sdir = get_student_dir(student_id)
    os.makedirs(sdir, exist_ok=True)
    
    # Find next available photo number
    photo_num = 1
    while True:
        img_path = os.path.join(sdir, f'{student_id}_{photo_num}{image_ext}')
        if not os.path.exists(img_path):
            break
        photo_num += 1
        
    try:
        with open(img_path, 'wb') as f:
            f.write(image_bytes)
            
        # Trigger training to update encodings
        try:
            # We import here to avoid circular imports if train_faces imports this module
            import sys
            sys.path.append(PROJECT_ROOT)
            from train_faces import train_faces
            train_faces()
        except Exception as e:
            logger.warning(f"Failed to trigger training: {e}")
            
        return True, img_path
    except Exception as e:
        return False, f'Failed to save image: {e}'


def rename_student_directory(old_id: str, new_id: str) -> bool:
    """Rename a student's directory when their username changes."""
    ensure_dataset_dirs()
    old_dir = get_student_dir(old_id)
    new_dir = get_student_dir(new_id)

    if os.path.exists(old_dir):
        try:
            os.rename(old_dir, new_dir)
            
            # Also rename the primary image if it exists
            old_img = os.path.join(new_dir, f'{old_id}.jpg')
            new_img = os.path.join(new_dir, f'{new_id}.jpg')
            if os.path.exists(old_img):
                os.rename(old_img, new_img)
                
            return True
        except Exception as e:
            logger.error(f"Failed to rename student directory: {e}")
            return False
    return True  # No directory to rename is considered success
