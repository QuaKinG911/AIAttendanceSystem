#!/usr/bin/env python3
"""
Train face recognition model from student photos.
Supports multiple photos per student and data augmentation.
"""
import os
import cv2
import numpy as np
from src.face_recognition.matcher import FaceMatcher
from src.config import config
import sqlite3


def augment_image(image):
    """Generate augmented versions of an image for better training"""
    augmented = [image]  # Original
    
    # Horizontal flip
    augmented.append(cv2.flip(image, 1))
    
    # Slight rotations
    h, w = image.shape[:2]
    for angle in [-10, 10]:
        M = cv2.getRotationMatrix2D((w/2, h/2), angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h))
        augmented.append(rotated)
    
    # Brightness adjustments
    for beta in [-20, 20]:
        adjusted = cv2.convertScaleAbs(image, alpha=1.0, beta=beta)
        augmented.append(adjusted)
    
    return augmented

def train_faces(incremental=True):
    print("--- Starting Face Training ---")

    # Initialize matcher
    matcher = FaceMatcher()

    # Load existing database if incremental
    db_path = config.get('recognition.database_path', 'data/face_encodings.pkl')
    if incremental and os.path.exists(db_path):
        matcher.load_known_faces(db_path)
        print(f"Loaded existing database with {len(matcher.known_face_encodings)} faces")

    # Build set of processed images
    processed_images = set()
    for meta in matcher.known_face_metadata:
        if meta and 'source_image' in meta:
            processed_images.add(meta['source_image'])
    
    print(f"Found {len(processed_images)} already processed images")

    faces_dir = 'data/faces'
    if not os.path.exists(faces_dir):
        print(f"Error: Faces directory '{faces_dir}' not found.")
        return

    count = 0
    errors = 0

    # Iterate through all student directories
    for username in os.listdir(faces_dir):
        user_dir = os.path.join(faces_dir, username)
        if not os.path.isdir(user_dir):
            continue

        print(f"Processing user: {username}")
        
        # Get User ID from database using sqlite3
        try:
            conn = sqlite3.connect('data/attendance.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                print(f"  Warning: User '{username}' not found in database. Skipping.")
                continue
                
            user_id = result[0]
            print(f"  Found user ID: {user_id}")
        except Exception as e:
            print(f"  Error querying database for {username}: {e}")
            continue

        # Find all image files for this student
        image_files = []
        for file in os.listdir(user_dir):
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_files.append(os.path.join(user_dir, file))

        if not image_files:
            print(f"  No photos found for {username}")
            continue

        print(f"  Found {len(image_files)} photo(s)")

        # Process each photo
        for img_path in image_files:
            try:
                # Check if already processed
                if img_path in processed_images:
                    print(f"  Skipping {os.path.basename(img_path)} (already processed)")
                    continue

                # Load image
                image = cv2.imread(img_path)
                if image is None:
                    print(f"  Failed to load image: {img_path}")
                    errors += 1
                    continue

                # Generate augmented versions
                augmented_images = augment_image(image)
                print(f"  Generated {len(augmented_images)} augmented versions")

                # Add each augmented version to matcher
                for aug_img in augmented_images:
                    success = matcher.add_known_face(aug_img, user_id, username, metadata={'source_image': img_path})
                    if success:
                        count += 1
                    else:
                        errors += 1

            except Exception as e:
                print(f"  Error processing {img_path}: {e}")
                errors += 1

    # Save the database
    if len(matcher.known_face_encodings) > 0:
        matcher.save_known_faces(db_path)
        print(f"\nTraining complete. Saved {len(matcher.known_face_encodings)} face encodings to {db_path}")
        if count > 0:
            print(f"Added {count} new face encodings")
        if errors > 0:
            print(f"Encountered {errors} errors during training")
    else:
        print("\nTraining complete. No faces were encoded.")

if __name__ == '__main__':
    train_faces()
