# app.py - Main Flask application with web routes

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, verify_jwt_in_request
from werkzeug.security import check_password_hash, generate_password_hash
import os
import logging
from datetime import datetime, date
import pandas as pd
from io import BytesIO

from src.api import create_app
from src.models import db, User, Class, Course, Enrollment, AttendanceSession, AttendanceRecord, UserRole
from src.scheduling import init_scheduler, shutdown_scheduler
from src.analytics import get_attendance_trends, get_student_performance

# Create Flask app
app = create_app()

# Override database URI for development
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data/attendance.db'

# Initialize database
with app.app_context():
    db.create_all()
    # Create default users if not exist
    if User.query.count() == 0:
        admin = User(username='admin', email='admin@school.edu', role=UserRole.ADMIN)
        admin.set_password('admin456')
        teacher = User(username='teacher1', email='teacher@school.edu', role=UserRole.TEACHER)
        teacher.set_password('teacher123')
        student = User(username='student1', email='student@school.edu', role=UserRole.STUDENT)
        student.set_password('student123')
        db.session.add_all([admin, teacher, student])
        db.session.commit()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Check database connection and users
with app.app_context():
    try:
        user_count = User.query.count()
        logging.info(f"Database connection successful. Found {user_count} users.")
        if user_count > 0:
            users = User.query.all()
            for user in users:
                logging.info(f"User: {user.username} (Role: {user.role.value})")
        else:
            logging.warning("No users found in database!")
    except Exception as e:
        logging.error(f"Database connection failed: {e}")

# Web routes (non-API)
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    logging.info(f"Login attempt - Method: {request.method}")

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        logging.info(f"Login attempt for username: {username}")

        user = User.query.filter_by(username=username).first()
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
                    return redirect(url_for('student_dashboard'))
                elif user.role.value == 'teacher':
                    logging.info("Redirecting to teacher dashboard")
                    return redirect(url_for('teacher_dashboard'))
                elif user.role.value == 'admin':
                    logging.info("Redirecting to admin dashboard")
                    return redirect(url_for('admin_dashboard'))
                else:
                    logging.error(f"Unknown role: {user.role.value}")
            else:
                logging.warning("Password check failed")
        else:
            logging.warning(f"User not found: {username}")

        logging.info("Login failed - showing error message")
        flash('Invalid credentials', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))

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

@app.route('/student/dashboard')
def student_dashboard():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('login'))
    return render_template('student_dashboard.html', user_role='student', username=session.get('username', 'student'))

@app.route('/teacher/dashboard')
def teacher_dashboard():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('login'))
    return render_template('teacher_dashboard.html', user_role='teacher', username=session.get('username', 'teacher'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html', user_role='admin', username=session.get('username', 'admin'))

@app.route('/admin/users')
def admin_users():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_users.html', user_role='admin', username=session.get('username', 'admin'))

@app.route('/admin/classes')
def admin_classes():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_classes.html', user_role='admin', username=session.get('username', 'admin'))

@app.route('/admin/analytics')
def admin_analytics():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_analytics.html', user_role='admin', username=session.get('username', 'admin'))

# API routes for web interface
@app.route('/api/classes')
@jwt_required()
def get_user_classes():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if current_user.role.value == 'student':
        classes = Class.query.join(Enrollment).filter(Enrollment.student_id == current_user_id).all()
    elif current_user.role.value == 'teacher':
        classes = Class.query.filter_by(teacher_id=current_user_id).all()
    else:  # admin
        classes = Class.query.all()

    return jsonify([{
        'id': c.id,
        'name': c.name,
        'start_time': c.start_time.strftime('%H:%M:%S'),
        'end_time': c.end_time.strftime('%H:%M:%S'),
        'room': c.room
    } for c in classes])

@app.route('/api/attendance/recent')
@jwt_required()
def get_recent_attendance():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if current_user.role.value != 'student':
        return jsonify([])

    # Get recent attendance records
    records = AttendanceRecord.query.filter_by(student_id=current_user_id).join(
        AttendanceSession
    ).order_by(AttendanceSession.session_date.desc()).limit(10).all()

    result = []
    for record in records:
        session = AttendanceSession.query.get(record.session_id)
        class_obj = Class.query.get(session.class_id)

        result.append({
            'date': session.session_date.isoformat(),
            'class_name': class_obj.name,
            'status': record.status.value,
            'time': record.detected_at.strftime('%H:%M:%S') if record.detected_at else None
        })

    return jsonify(result)

@app.route('/api/analytics/trends')
@jwt_required()
def get_trends():
    days = int(request.args.get('days', 30))
    trends = get_attendance_trends(days)
    return jsonify(trends)

@app.route('/api/analytics/anomalies')
@jwt_required()
def get_anomalies():
    # Simple anomaly detection
    today = date.today()
    sessions = AttendanceSession.query.filter_by(session_date=today).all()

    anomalies = []
    for session in sessions:
        records = AttendanceRecord.query.filter_by(session_id=session.id).all()
        present_rate = len([r for r in records if r.status.value in ['present', 'late']]) / max(len(records), 1)

        if present_rate < 0.5:  # Less than 50% attendance
            anomalies.append({
                'type': 'low_attendance',
                'class_id': session.class_id,
                'message': f'Only {present_rate*100:.1f}% attendance recorded'
            })

    return jsonify(anomalies)

@app.route('/api/analytics/export')
def export_attendance():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    # Export attendance data to Excel
    records = AttendanceRecord.query.join(AttendanceSession).join(Class).all()

    data = []
    for record in records:
        attendance_session = AttendanceSession.query.get(record.session_id)
        class_obj = Class.query.get(attendance_session.class_id)
        student = User.query.get(record.student_id)

        data.append({
            'Date': attendance_session.session_date,
            'Class': class_obj.name,
            'Student': student.username,
            'Status': record.status.value,
            'Time': record.detected_at,
            'Confidence': float(record.confidence_score) if record.confidence_score else None
        })

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Attendance', index=False)

    output.seek(0)
    return send_file(output, download_name='attendance_export.xlsx', as_attachment=True)

# Admin API routes
@app.route('/api/admin/users', methods=['GET', 'POST'])
def admin_users_api():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'student')

        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already exists'}), 400

        user = User(
            username=username,
            email=email,
            role=UserRole(role)
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        return jsonify({'message': 'User created successfully', 'user_id': user.id})

    # GET request
    users = User.query.all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'role': u.role.value,
        'created_at': u.created_at.isoformat()
    } for u in users])

@app.route('/api/admin/users/<int:user_id>', methods=['PUT', 'DELETE'])
def admin_user_api(user_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    user = User.query.get_or_404(user_id)

    if request.method == 'DELETE':
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'})

    elif request.method == 'PUT':
        data = request.get_json()
        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        if 'role' in data:
            user.role = UserRole(data['role'])
        db.session.commit()
        return jsonify({'message': 'User updated successfully'})

@app.route('/api/admin/classes', methods=['GET', 'POST'])
def admin_classes_api():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name')

        class_obj = Class(name=name)
        db.session.add(class_obj)
        db.session.commit()

        return jsonify({'message': 'Class created successfully', 'class_id': class_obj.id})

    # GET request
    classes = Class.query.all()
    result = []
    for c in classes:
        courses = Course.query.filter_by(class_id=c.id).all()
        course_list = []
        for course in courses:
            teacher = User.query.get(course.teacher_id)
            course_list.append({
                'id': course.id,
                'name': course.name,
                'teacher': teacher.username if teacher else 'Unknown',
                'start_time': course.start_time.strftime('%H:%M'),
                'end_time': course.end_time.strftime('%H:%M'),
                'room': course.room,
                'day_of_week': course.day_of_week
            })
        result.append({
            'id': c.id,
            'name': c.name,
            'courses': course_list,
            'student_count': Enrollment.query.filter_by(class_id=c.id).count()
        })
    return jsonify(result)

@app.route('/api/admin/classes/<int:class_id>', methods=['PUT', 'DELETE'])
def admin_class_api(class_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    class_obj = Class.query.get_or_404(class_id)

    if request.method == 'DELETE':
        # Delete courses and enrollments first
        Course.query.filter_by(class_id=class_id).delete()
        Enrollment.query.filter_by(class_id=class_id).delete()
        db.session.delete(class_obj)
        db.session.commit()
        return jsonify({'message': 'Class deleted successfully'})

    elif request.method == 'PUT':
        data = request.get_json()
        class_obj.name = data.get('name', class_obj.name)
        db.session.commit()
        return jsonify({'message': 'Class updated successfully'})

@app.route('/api/admin/classes/<int:class_id>/enroll', methods=['POST', 'DELETE'])
def admin_class_enroll_api(class_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    class_obj = Class.query.get_or_404(class_id)
    data = request.get_json()
    student_id = data.get('student_id')

    if not student_id:
        return jsonify({'error': 'Student ID required'}), 400

    student = User.query.get_or_404(student_id)
    if student.role.value != 'student':
        return jsonify({'error': 'User is not a student'}), 400

    if request.method == 'POST':
        # Check if already enrolled
        existing = Enrollment.query.filter_by(class_id=class_id, student_id=student_id).first()
        if existing:
            return jsonify({'error': 'Student already enrolled'}), 400

        enrollment = Enrollment(class_id=class_id, student_id=student_id)
        db.session.add(enrollment)
        db.session.commit()
        return jsonify({'message': 'Student enrolled successfully'})

    elif request.method == 'DELETE':
        enrollment = Enrollment.query.filter_by(class_id=class_id, student_id=student_id).first()
        if not enrollment:
            return jsonify({'error': 'Student not enrolled'}), 404

        db.session.delete(enrollment)
        db.session.commit()
        return jsonify({'message': 'Student unenrolled successfully'})

@app.route('/api/admin/classes/<int:class_id>/students')
def admin_class_students_api(class_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    class_obj = Class.query.get_or_404(class_id)
    enrollments = Enrollment.query.filter_by(class_id=class_id).all()

    students = []
    for enrollment in enrollments:
        student = User.query.get(enrollment.student_id)
        if student:
            students.append({
                'id': student.id,
                'username': student.username,
                'email': student.email
            })

    return jsonify(students)

@app.route('/api/admin/students')
def admin_students_api():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    students = User.query.filter_by(role=UserRole.STUDENT).all()
    return jsonify([{
        'id': s.id,
        'username': s.username,
        'email': s.email
    } for s in students])

@app.route('/api/admin/classes/<int:class_id>/courses', methods=['GET', 'POST'])
def admin_class_courses_api(class_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    class_obj = Class.query.get_or_404(class_id)

    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        teacher_id = data.get('teacher_id')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        room = data.get('room', '')
        day_of_week = data.get('day_of_week')

        # Validate teacher exists
        teacher = User.query.get(teacher_id)
        if not teacher or teacher.role.value != 'teacher':
            return jsonify({'error': 'Invalid teacher'}), 400

        from datetime import datetime
        course = Course(
            class_id=class_id,
            name=name,
            teacher_id=teacher_id,
            start_time=datetime.strptime(start_time, '%H:%M').time(),
            end_time=datetime.strptime(end_time, '%H:%M').time(),
            room=room,
            day_of_week=day_of_week
        )
        db.session.add(course)
        db.session.commit()

        return jsonify({'message': 'Course created successfully', 'course_id': course.id})

    # GET request
    courses = Course.query.filter_by(class_id=class_id).all()
    result = []
    for c in courses:
        teacher = User.query.get(c.teacher_id)
        result.append({
            'id': c.id,
            'name': c.name,
            'teacher': teacher.username if teacher else 'Unknown',
            'start_time': c.start_time.strftime('%H:%M'),
            'end_time': c.end_time.strftime('%H:%M'),
            'room': c.room,
            'day_of_week': c.day_of_week
        })
    return jsonify(result)

@app.route('/api/admin/classes/<int:class_id>/courses/<int:course_id>', methods=['PUT', 'DELETE'])
def admin_course_api(class_id, course_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    course = Course.query.filter_by(id=course_id, class_id=class_id).first_or_404()

    if request.method == 'DELETE':
        db.session.delete(course)
        db.session.commit()
        return jsonify({'message': 'Course deleted successfully'})

    elif request.method == 'PUT':
        data = request.get_json()
        course.name = data.get('name', course.name)
        course.teacher_id = data.get('teacher_id', course.teacher_id)
        if 'start_time' in data:
            course.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        if 'end_time' in data:
            course.end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        course.room = data.get('room', course.room)
        course.day_of_week = data.get('day_of_week', course.day_of_week)
        db.session.commit()
        return jsonify({'message': 'Course updated successfully'})

@app.route('/api/admin/teachers')
def admin_teachers_api():
    logging.info("admin_teachers_api called")
    logging.info(f"Session user_id: {session.get('user_id')}, role: {session.get('role')}")

    if 'user_id' not in session or session.get('role') != 'admin':
        logging.warning("Unauthorized access to admin_teachers_api")
        return jsonify({'error': 'Unauthorized'}), 403

    teachers = User.query.filter_by(role=UserRole.TEACHER).all()
    logging.info(f"Found {len(teachers)} teachers")
    result = [{
        'id': t.id,
        'username': t.username,
        'email': t.email
    } for t in teachers]
    logging.info(f"Returning teachers: {result}")
    return jsonify(result)

@app.route('/api/admin/stats')
def admin_stats_api():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    total_users = User.query.count()
    total_classes = Class.query.count()
    today = date.today()
    today_sessions = AttendanceSession.query.filter_by(session_date=today).count()

    # Calculate average attendance rate
    recent_sessions = AttendanceSession.query.limit(100).all()
    if recent_sessions:
        total_records = 0
        present_count = 0
        for session in recent_sessions:
            records = AttendanceRecord.query.filter_by(session_id=session.id).all()
            total_records += len(records)
            present_count += len([r for r in records if r.status.value in ['present', 'late']])

        avg_rate = (present_count / max(total_records, 1)) * 100
    else:
        avg_rate = 0

    return jsonify({
        'total_users': total_users,
        'total_classes': total_classes,
        'today_sessions': today_sessions,
        'avg_attendance_rate': round(avg_rate, 1)
    })

# Initialize scheduler on startup (will be called in run_web.py)

# Cleanup on shutdown
@app.teardown_appcontext
def shutdown_app(exception=None):
    shutdown_scheduler()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)