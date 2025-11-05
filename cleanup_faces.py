#!/usr/bin/env python3
"""
Clean up duplicate face images and create proper dataset
"""

import os
import json
import cv2
import numpy as np
from pathlib import Path

def cleanup_duplicate_faces():
    """Remove duplicate face images and clean up dataset"""
    print("🧹 Cleaning up duplicate face images...")
    print("=" * 50)

    faces_dir = Path('data/faces')
    students_file = faces_dir / 'students.json'

    if not students_file.exists():
        print("❌ students.json not found")
        return

    # Load current students
    with open(students_file, 'r') as f:
        students = json.load(f)

    print(f"Current students: {list(students.keys())}")

    # Check for duplicate images
    image_hashes = {}
    duplicates = []

    for student_id, info in students.items():
        student_dir = faces_dir / student_id
        if not student_dir.exists():
            continue

        # Find image file
        image_files = list(student_dir.glob('*.jpg')) + list(student_dir.glob('*.jpeg')) + list(student_dir.glob('*.png'))
        if not image_files:
            continue

        image_path = image_files[0]

        # Calculate image hash
        img = cv2.imread(str(image_path))
        if img is None:
            continue

        # Simple hash based on image content
        img_hash = hash(img.tobytes())

        if img_hash in image_hashes:
            duplicates.append((student_id, image_hashes[img_hash]))
            print(f"⚠️  {student_id} is duplicate of {image_hashes[img_hash]}")
        else:
            image_hashes[img_hash] = student_id

    # Keep only unique students
    if duplicates:
        print(f"\n🗑️  Removing {len(duplicates)} duplicate entries...")

        # Remove duplicate directories
        for dup_id, original_id in duplicates:
            dup_dir = faces_dir / dup_id
            if dup_dir.exists():
                import shutil
                shutil.rmtree(dup_dir)
                print(f"  Removed duplicate: {dup_id}")

            # Remove from students dict
            if dup_id in students:
                del students[dup_id]

        # Save cleaned students.json
        with open(students_file, 'w') as f:
            json.dump(students, f, indent=2)

        print(f"✅ Cleaned dataset. Remaining students: {list(students.keys())}")

    # Recreate face database
    print("\n🔄 Recreating face database...")
    os.system('python create_face_database.py')

    print("✅ Cleanup complete!")

if __name__ == "__main__":
    cleanup_duplicate_faces()