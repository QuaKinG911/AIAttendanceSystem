import os
import shutil
import sys
from pathlib import Path

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = PROJECT_ROOT / 'models'


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(dest, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)


def ensure_haar_cascade() -> Path:
    target = MODELS_DIR / 'haarcascade_frontalface_default.xml'
    if target.exists():
        return target
    # If file exists in project root, move it into models/ and leave a symlink for compatibility
    root_copy = PROJECT_ROOT / 'haarcascade_frontalface_default.xml'
    if root_copy.exists():
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        shutil.move(str(root_copy), str(target))
        try:
            root_copy.symlink_to(target)
        except Exception:
            pass
        return target
    # Otherwise fetch from OpenCV
    url = 'https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml'
    download(url, target)
    # Best effort compatibility symlink
    try:
        (PROJECT_ROOT / 'haarcascade_frontalface_default.xml').symlink_to(target)
    except Exception:
        pass
    return target


def ensure_opencv_yunet() -> Path:
    """Download a lightweight ONNX face detector from OpenCV Zoo (YuNet)."""
    target = MODELS_DIR / 'face_detection_yunet_2023mar.onnx'
    if target.exists():
        return target
    url = 'https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx'
    download(url, target)
    return target


def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    cascade = ensure_haar_cascade()
    yunet = ensure_opencv_yunet()
    print('Models ready:')
    print(' -', cascade)
    print(' -', yunet)


if __name__ == '__main__':
    main()


