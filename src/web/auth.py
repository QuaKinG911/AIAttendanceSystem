from flask import render_template, request, redirect, url_for, flash, session, jsonify
from src.models import db, User, UserRole, FaceEncoding
from . import web_auth_bp
import logging

@web_auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    logging.info(f"Login attempt - Method: {request.method}")

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        logging.info(f"Login attempt for email: {username}")

        user = User.query.filter_by(email=username).first()
        logging.info(f"User found: {user is not None}")

        if user:
            logging.info(f"User details - ID: {user.id}, Role: {user.role.value}")
            password_valid = user.check_password(password)
            logging.info(f"Password check result: {password_valid}")

            if password_valid:
                # Set session
                session['user_id'] = user.id
                session['username'] = user.username
                session['role'] = user.role.value
                logging.info(f"Session set - user_id: {session['user_id']}, role: {session['role']}")

                # Redirect to appropriate dashboard
                if user.role.value == 'student':
                    logging.info("Redirecting to student dashboard")
                    return redirect(url_for('web_student.student_dashboard'))
                elif user.role.value == 'teacher':
                    logging.info("Redirecting to teacher dashboard")
                    return redirect(url_for('web_teacher.teacher_dashboard'))
                elif user.role.value == 'admin':
                    logging.info("Redirecting to admin dashboard")
                    return redirect(url_for('web_admin.admin_dashboard'))
                else:
                    logging.error(f"Unknown role: {user.role.value}")
            else:
                logging.warning("Password check failed")
        else:
            logging.warning(f"User not found: {username}")

        logging.info("Login failed - showing error message")
        flash('Invalid credentials', 'error')

    return render_template('login.html')

@web_auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('web_auth.login'))

from src.utils.dataset_manager import save_student_photo, get_student_dir, add_student, rename_student_directory

@web_auth_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('web_auth.login'))

    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('web_auth.login'))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_profile':
            new_username = request.form.get('username')
            new_email = request.form.get('email')

            if new_username and new_email:
                # Check if username or email is already taken by another user
                existing_user = User.query.filter(
                    (User.username == new_username) | (User.email == new_email)
                ).filter(User.id != user.id).first()

                if existing_user:
                    if existing_user.username == new_username:
                        flash('Username already taken', 'error')
                    else:
                        flash('Email already taken', 'error')
                else:
                    # Rename directory if username changed
                    if user.username != new_username:
                        rename_student_directory(user.username, new_username)
                    
                    user.username = new_username
                    user.email = new_email
                    db.session.commit()
                    session['username'] = new_username  # Update session
                    flash('Profile updated successfully', 'success')
            else:
                flash('Username and Email are required', 'error')

        elif action == 'update_password':
            # Update password
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            if current_password and new_password:
                if not user.check_password(current_password):
                    flash('Current password is incorrect', 'error')
                elif new_password != confirm_password:
                    flash('New passwords do not match', 'error')
                else:
                    user.set_password(new_password)
                    db.session.commit()
                    flash('Password updated successfully', 'success')
            else:
                flash('Please fill in all password fields', 'error')
        
        else:
             # Fallback for legacy or unspecified action (assume password update if password fields present)
            if request.form.get('current_password'):
                 current_password = request.form.get('current_password')
                 new_password = request.form.get('new_password')
                 confirm_password = request.form.get('confirm_password')

                 if current_password and new_password:
                    if not user.check_password(current_password):
                        flash('Current password is incorrect', 'error')
                    elif new_password != confirm_password:
                        flash('New passwords do not match', 'error')
                    else:
                        user.set_password(new_password)
                        db.session.commit()
                        flash('Password updated successfully', 'success')
            else:
                flash('Invalid action', 'error')

    # Get face encoding
    face_encoding = FaceEncoding.query.filter_by(student_id=user.id).first()

    return render_template('profile.html', 
                         user=user, 
                         face_encoding=face_encoding,
                         user_role=session.get('role'),
                         username=session.get('username'))

import os
from werkzeug.utils import secure_filename

from flask import send_file

@web_auth_bp.route('/profile/upload-photo', methods=['POST'])
def upload_photo():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if 'photo' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['photo']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        try:
            user_id = session['user_id']
            user = User.query.get(user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404

            # Read file bytes
            image_bytes = file.read()
            
            # Save using dataset manager (saves to data/faces/{username}/{username}.jpg)
            # We use add_student to ensure it overwrites the primary image
            success, result = add_student(user.username, user.full_name or user.username, image_bytes)
            
            if not success:
                return jsonify({'error': result}), 500
            
            # Update or create FaceEncoding record
            # We set image_path to None so the system looks in data/faces (default location)
            encoding_record = FaceEncoding.query.filter_by(student_id=user_id).first()
            if not encoding_record:
                encoding_record = FaceEncoding(
                    student_id=user_id,
                    encoding=b'placeholder', # Placeholder until processed
                    image_path=None 
                )
                db.session.add(encoding_record)
            else:
                encoding_record.image_path = None # Clear custom upload path to use default
            
            db.session.commit()
            return jsonify({'success': True})
            
        except Exception as e:
            logging.error(f"Photo upload error: {str(e)}")
            return jsonify({'error': 'Failed to upload photo'}), 500

@web_auth_bp.route('/profile/photo')
def get_my_photo():
    """Serve the current user's profile photo"""
    if 'user_id' not in session:
        return redirect(url_for('web_auth.login'))
        
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    # Check data/faces/{username}/{username}.jpg
    photo_path = os.path.join(os.getcwd(), 'data', 'faces', user.username, f"{user.username}.jpg")
    
    if os.path.exists(photo_path):
        return send_file(photo_path, mimetype='image/jpeg')
    else:
        # Return default avatar
        return send_file(os.path.join(os.getcwd(), 'static', 'images', 'default-avatar.svg'), mimetype='image/svg+xml')
