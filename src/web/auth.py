from flask import render_template, request, redirect, url_for, flash, session
from src.models import db, User, UserRole
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

@web_auth_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('web_auth.login'))

    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('web_auth.login'))

    if request.method == 'POST':
        # Update profile
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

    return render_template('profile.html', user=user)
