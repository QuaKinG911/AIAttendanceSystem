# src/api/admin.py - Admin API endpoints

from flask import Blueprint, request, jsonify, send_file, session, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from src.models import User, UserRole, Class, Course, Enrollment, AttendanceSession, AttendanceRecord, db
import os
from datetime import datetime, timedelta, date
import pandas as pd
from io import BytesIO
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_or_session_required(f):
    """Decorator that allows either JWT auth or session auth for admin users"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Try JWT first
        try:
            jwt_user = get_jwt_identity()
            if jwt_user:
                user = User.query.filter_by(username=jwt_user).first()
                if user and user.role == UserRole.ADMIN:
                    g.user = user
                    return f(*args, **kwargs)
        except:
            pass

        # Fall back to session auth
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if user and user.role == UserRole.ADMIN:
                g.user = user
                return f(*args, **kwargs)

        return jsonify({'error': 'Authentication required'}), 401

    return decorated_function

@admin_bp.route('/stats', methods=['GET'])
@admin_or_session_required
def get_stats():
    """Get admin dashboard statistics"""
    try:
        # Total users by role
        total_users = User.query.count()
        total_students = User.query.filter_by(role=UserRole.STUDENT).count()
        total_teachers = User.query.filter_by(role=UserRole.TEACHER).count()
        total_admins = User.query.filter_by(role=UserRole.ADMIN).count()

        # Total classes
        total_classes = Class.query.count()

        # Today's sessions
        today = datetime.now().date()
        today_sessions = AttendanceSession.query.filter(
            func.date(AttendanceSession.start_time) == today
        ).count()

        # Average attendance rate (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_records = AttendanceRecord.query.filter(
            AttendanceRecord.detected_at >= thirty_days_ago
        ).all()

        if recent_records:
            total_records = len(recent_records)
            present_count = sum(1 for r in recent_records if r.status == 'present')
            avg_attendance_rate = round((present_count / total_records) * 100, 1) if total_records > 0 else 0
        else:
            avg_attendance_rate = 0

        return jsonify({
            'total_users': total_users,
            'total_students': total_students,
            'total_teachers': total_teachers,
            'total_admins': total_admins,
            'total_classes': total_classes,
            'today_sessions': today_sessions,
            'avg_attendance_rate': avg_attendance_rate
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users', methods=['GET'])
@admin_or_session_required
def get_users():
    """Get users filtered by role"""
    try:
        role = request.args.get('role')
        if role:
            users = User.query.filter_by(role=UserRole(role)).all()
        else:
            users = User.query.all()

        return jsonify({
            'users': [{
                'id': u.id,
                'username': u.username,
                'email': u.email,
                'role': u.role.value,
                'full_name': u.full_name,
                'gender': u.gender,
                'major': u.major,
                'grade': u.start_year,
                'birthday': u.birthday.isoformat() if u.birthday else None,
                'degree_level': u.degree_level,
                'created_at': u.created_at.isoformat() if u.created_at else None
            } for u in users]
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users', methods=['POST'])
@admin_or_session_required
def create_user():
    """Create a new user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Check if email already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400

        user = User()
        user.username = data.get('username', data['email'].split('@')[0])
        user.email = data['email']
        user.role = UserRole(data['role'])
        user.set_password(data['password'])

        # Optional fields
        if 'full_name' in data:
            user.full_name = data['full_name']
        if 'gender' in data:
            user.gender = data['gender']
        if 'major' in data:
            user.major = data['major']
        if 'grade' in data:
            user.start_year = data['grade']
        if 'birthday' in data:
            try:
                user.birthday = date.fromisoformat(data['birthday'])
            except (ValueError, TypeError):
                user.birthday = None
        if 'degree_level' in data:
            user.degree_level = data['degree_level']

        db.session.add(user)
        db.session.commit()

        return jsonify({'message': 'User created successfully', 'user_id': user.id}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_or_session_required
def update_user(user_id):
    """Update a user"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()

        if 'email' in data and data['email'] != user.email:
            if User.query.filter_by(email=data['email']).first():
                return jsonify({'error': 'Email already exists'}), 400
            user.email = data['email']

        if 'username' in data:
            user.username = data['username']
        if 'role' in data:
            user.role = UserRole(data['role'])
        if 'password' in data and data['password']:
            user.set_password(data['password'])

        # Optional fields
        if 'full_name' in data:
            user.full_name = data['full_name']
        if 'gender' in data:
            user.gender = data['gender']
        if 'major' in data:
            user.major = data['major']
        if 'grade' in data:
            user.start_year = data['grade']
        if 'birthday' in data:
            try:
                user.birthday = date.fromisoformat(data['birthday'])
            except (ValueError, TypeError):
                user.birthday = None
        if 'degree_level' in data:
            user.degree_level = data['degree_level']

        db.session.commit()

        return jsonify({'message': 'User updated successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_or_session_required
def delete_user(user_id):
    """Delete a user"""
    try:
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()

        return jsonify({'message': 'User deleted successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/teachers', methods=['GET'])
@admin_or_session_required
def get_teachers():
    """Get all teachers with their courses"""
    try:
        teachers = User.query.filter_by(role=UserRole.TEACHER).all()
        result = []

        for teacher in teachers:
            # Get courses taught by this teacher
            courses = Course.query.filter_by(teacher_id=teacher.id).all()
            course_names = [course.name for course in courses]

            result.append({
                'id': teacher.id,
                'username': teacher.username,
                'email': teacher.email,
                'full_name': teacher.full_name,
                'courses': course_names
            })

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/classes', methods=['GET'])
@admin_or_session_required
def get_classes():
    """Get all classes with detailed information"""
    try:
        classes = Class.query.all()
        result = []

        for c in classes:
            # Get enrolled students count
            student_count = Enrollment.query.filter_by(class_id=c.id).count()

            # Get courses for this class
            courses = Course.query.filter_by(class_id=c.id).all()
            courses_data = []

            for course in courses:
                # Get teacher info
                teacher = User.query.get(course.teacher_id)
                teacher_name = teacher.full_name or teacher.username if teacher else "Unknown"

                courses_data.append({
                    'id': course.id,
                    'name': course.name,
                    'teacher_id': course.teacher_id,
                    'teacher_name': teacher_name,
                    'start_time': course.start_time.strftime('%H:%M') if course.start_time else None,
                    'end_time': course.end_time.strftime('%H:%M') if course.end_time else None,
                    'room': course.room,
                    'day_of_week': course.day_of_week
                })

            result.append({
                'id': c.id,
                'name': c.name,
                'student_count': student_count,
                'courses': courses_data,
                'created_at': c.created_at.isoformat() if c.created_at else None
            })

        return jsonify({'classes': result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/classes', methods=['POST'])
@admin_or_session_required
def create_class():
    """Create a new class"""
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'Class name is required'}), 400

        # Check if class with this name already exists
        if Class.query.filter_by(name=data['name']).first():
            return jsonify({'error': 'Class with this name already exists'}), 400

        new_class = Class()
        new_class.name = data['name']
        db.session.add(new_class)
        db.session.commit()

        return jsonify({
            'message': 'Class created successfully',
            'class_id': new_class.id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/classes/<int:class_id>', methods=['PUT'])
@admin_or_session_required
def update_class(class_id):
    """Update a class"""
    try:
        class_obj = Class.query.get_or_404(class_id)
        data = request.get_json()

        if 'name' in data:
            # Check if another class with this name exists
            existing = Class.query.filter_by(name=data['name']).first()
            if existing and existing.id != class_id:
                return jsonify({'error': 'Class with this name already exists'}), 400
            class_obj.name = data['name']

        db.session.commit()

        return jsonify({'message': 'Class updated successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/classes/<int:class_id>', methods=['DELETE'])
@admin_or_session_required
def delete_class(class_id):
    """Delete a class"""
    try:
        class_obj = Class.query.get_or_404(class_id)

        # Delete related enrollments and courses
        Enrollment.query.filter_by(class_id=class_id).delete()
        Course.query.filter_by(class_id=class_id).delete()

        db.session.delete(class_obj)
        db.session.commit()

        return jsonify({'message': 'Class deleted successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/classes/enroll', methods=['POST'])
@admin_or_session_required
def enroll_student():
    """Enroll a student in a class"""
    try:
        data = request.get_json()
        if not data or 'class_id' not in data or 'student_id' not in data:
            return jsonify({'error': 'class_id and student_id are required'}), 400

        class_id = data['class_id']
        student_id = data['student_id']

        # Check if class exists
        class_obj = Class.query.get(class_id)
        if not class_obj:
            return jsonify({'error': 'Class not found'}), 404

        # Check if student exists and is a student
        student = User.query.get(student_id)
        if not student or student.role != UserRole.STUDENT:
            return jsonify({'error': 'Invalid student'}), 400

        # Check if already enrolled
        existing = Enrollment.query.filter_by(class_id=class_id, student_id=student_id).first()
        if existing:
            return jsonify({'error': 'Student already enrolled in this class'}), 400

        enrollment = Enrollment()
        enrollment.class_id = class_id
        enrollment.student_id = student_id
        db.session.add(enrollment)
        db.session.commit()

        return jsonify({'message': 'Student enrolled successfully'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/students/<int:student_id>/photo', methods=['GET'])
@admin_or_session_required
def get_student_photo(student_id):
    """Get student photo"""
    try:
        student = User.query.filter_by(id=student_id, role=UserRole.STUDENT).first_or_404()

        # Check if photo exists
        photo_path = f"data/faces/{student.username}/{student.username}.jpg"
        if os.path.exists(photo_path):
            return send_file(photo_path, mimetype='image/jpeg')
        else:
            # Return default avatar
            return send_file('static/images/default-avatar.svg', mimetype='image/svg+xml')

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/attendance/analysis', methods=['GET'])
@admin_or_session_required
def get_attendance_analysis():
    """Get attendance analysis for all students"""
    try:
        # Get all students
        students = User.query.filter_by(role=UserRole.STUDENT).all()

        student_details = []
        low_attendance_students = []
        total_students = len(students)
        total_sessions_overall = 0
        total_present_overall = 0

        for student in students:
            # Get attendance records for this student
            records = AttendanceRecord.query.filter_by(student_id=student.id).all()

            total_sessions = len(records)
            present_count = sum(1 for r in records if r.status == 'present')
            absent_count = sum(1 for r in records if r.status == 'absent')
            late_count = sum(1 for r in records if r.status == 'late')

            attendance_rate = round((present_count / total_sessions) * 100, 1) if total_sessions > 0 else 0

            student_details.append({
                'id': student.id,
                'name': student.full_name or student.username,
                'total_sessions': total_sessions,
                'present_count': present_count,
                'absent_count': absent_count,
                'late_count': late_count,
                'attendance_rate': attendance_rate
            })

            if attendance_rate < 70:
                low_attendance_students.append({
                    'id': student.id,
                    'name': student.full_name or student.username,
                    'attendance_rate': attendance_rate
                })

            total_sessions_overall += total_sessions
            total_present_overall += present_count

        avg_attendance = round((total_present_overall / total_sessions_overall) * 100, 1) if total_sessions_overall > 0 else 0

        return jsonify({
            'total_students': total_students,
            'avg_attendance': avg_attendance,
            'low_attendance_count': len(low_attendance_students),
            'total_sessions': total_sessions_overall,
            'student_details': student_details,
            'low_attendance_students': low_attendance_students
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/attendance/export', methods=['GET'])
@admin_or_session_required
def export_attendance():
    """Export attendance data as JSON"""
    try:
        # Get attendance data
        records = AttendanceRecord.query.join(User).add_columns(
            User.username, User.full_name, User.email,
            AttendanceRecord.detected_at, AttendanceRecord.status, AttendanceRecord.confidence_score
        ).all()

        # Create data
        data = [{
            'student_username': record.username,
            'student_name': record.full_name or record.username,
            'email': record.email,
            'timestamp': record.detected_at.isoformat() if record.detected_at else None,
            'status': record.status.value if record.status else None,
            'confidence': float(record.confidence_score) if record.confidence_score else None
        } for record in records]

        return jsonify({
            'attendance_records': data,
            'total_records': len(data)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500