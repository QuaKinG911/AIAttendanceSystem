import os
import json
from typing import Dict, List, Optional, Tuple


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
# New canonical folder for recognition reference images
DATASET_DIR = os.path.join(PROJECT_ROOT, 'data', 'faces')
STUDENTS_JSON = os.path.join(DATASET_DIR, 'students.json')


def ensure_dataset_dirs() -> None:
    os.makedirs(DATASET_DIR, exist_ok=True)
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
    """Save a photo for an existing student.

    Returns (ok, path_or_error)
    """
    ensure_dataset_dirs()
    if not student_id:
        return False, 'Student ID is required'

    sdir = get_student_dir(student_id)
    os.makedirs(sdir, exist_ok=True)
    img_path = os.path.join(sdir, f'{student_id}{image_ext}')
    try:
        with open(img_path, 'wb') as f:
            f.write(image_bytes)
        return True, img_path
    except Exception as e:
        return False, f'Failed to save image: {e}'

