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
        if 'nationality' in data:
            user.nationality = data['nationality']
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
        if 'courses' in data:
            user.courses = data['courses']

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
        if 'nationality' in data:
            user.nationality = data['nationality']
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
        if 'courses' in data:
            user.courses = data['courses']

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
            # Prioritize the courses JSON field if available
            if teacher.courses:
                course_names = teacher.courses
            else:
                courses = Course.query.filter_by(teacher_id=teacher.id).all()
                course_names = [course.name for course in courses]

            result.append({
                'id': teacher.id,
                'username': teacher.username,
                'email': teacher.email,
                'full_name': teacher.full_name,
                'nationality': teacher.nationality,
                'birthday': teacher.birthday.isoformat() if teacher.birthday else None,
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
        db.session.flush()  # Flush to get the new_class.id

        # Handle student enrollment
        if 'student_ids' in data and isinstance(data['student_ids'], list):
            for student_id in data['student_ids']:
                # Verify student exists and is a student
                student = User.query.get(student_id)
                if student and student.role == UserRole.STUDENT:
                    enrollment = Enrollment(class_id=new_class.id, student_id=student_id)
                    db.session.add(enrollment)

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
    """Enroll a student or multiple students in a class"""
    try:
        data = request.get_json()
        if not data or 'class_id' not in data:
            return jsonify({'error': 'class_id is required'}), 400

        class_id = data['class_id']
        
        # Check if class exists
        class_obj = Class.query.get(class_id)
        if not class_obj:
            return jsonify({'error': 'Class not found'}), 404

        student_ids = []
        if 'student_ids' in data and isinstance(data['student_ids'], list):
            student_ids = data['student_ids']
        elif 'student_id' in data:
            student_ids = [data['student_id']]
        else:
            return jsonify({'error': 'student_id or student_ids required'}), 400

        enrolled_count = 0
        for student_id in student_ids:
            # Check if student exists and is a student
            student = User.query.get(student_id)
            if not student or student.role != UserRole.STUDENT:
                continue

            # Check if already enrolled
            existing = Enrollment.query.filter_by(class_id=class_id, student_id=student_id).first()
            if existing:
                continue

            enrollment = Enrollment()
            enrollment.class_id = class_id
            enrollment.student_id = student_id
            db.session.add(enrollment)
            enrolled_count += 1

        db.session.commit()

        return jsonify({'message': f'{enrolled_count} students enrolled successfully'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/classes/<int:class_id>/students', methods=['GET'])
@admin_or_session_required
def get_class_students(class_id):
    """Get all students enrolled in a class"""
    try:
        class_obj = Class.query.get_or_404(class_id)
        
        enrollments = Enrollment.query.filter_by(class_id=class_id).all()
        students = []
        for enrollment in enrollments:
            student = User.query.get(enrollment.student_id)
            if student:
                students.append({
                    'id': student.id,
                    'username': student.username,
                    'full_name': student.full_name,
                    'email': student.email,
                    'enrolled_at': enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else None
                })
        
        return jsonify({'students': students})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/classes/courses/assign', methods=['POST'])
@admin_or_session_required
def assign_courses():
    """Assign courses to a class"""
    try:
        data = request.get_json()
        if not data or 'class_id' not in data or 'courses' not in data:
            return jsonify({'error': 'class_id and courses are required'}), 400

        class_id = data['class_id']
        courses_list = data['courses']

        # Check if class exists
        class_obj = Class.query.get(class_id)
        if not class_obj:
            return jsonify({'error': 'Class not found'}), 404

        created_count = 0
        for course_data in courses_list:
            # course_data should contain: name, teacher_id, start_time, end_time, day_of_week, room
            # For now, we'll create a basic course entry. 
            # In a real scenario, we'd need more details like schedule.
            # Assuming the frontend sends just names and we need to find the teacher who teaches it.
            
            course_name = course_data.get('name')
            teacher_id = course_data.get('teacher_id')
            
            if not course_name or not teacher_id:
                continue

            # Check if course already assigned to this class
            existing_course = Course.query.filter_by(
                class_id=class_id, 
                name=course_name,
                teacher_id=teacher_id
            ).first()
            
            if existing_course:
                continue

            # Create a new Course instance
            # Note: This requires the frontend to provide schedule details or defaults
            # For this fix, we will use default values if not provided, 
            # but ideally the UI should ask for schedule.
            
            # Set default semester dates (current date to +4 months)
            today = datetime.now().date()

            new_course = Course(
                class_id=class_id,
                name=course_name,
                teacher_id=teacher_id,
                start_time=datetime.strptime('00:00', '%H:%M').time(),
                end_time=datetime.strptime('00:00', '%H:%M').time(),
                day_of_week=6, # Sunday (Placeholder)
                room='TBD',
                start_date=today,
                end_date=today + timedelta(days=120)
            )
            
            db.session.add(new_course)
            created_count += 1

        db.session.commit()

        return jsonify({'message': f'{created_count} courses assigned successfully'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/classes/<int:class_id>/courses/<int:course_id>', methods=['DELETE'])
@admin_or_session_required
def remove_course_from_class(class_id, course_id):
    """Remove a course from a class"""
    try:
        course = Course.query.filter_by(id=course_id, class_id=class_id).first_or_404()
        db.session.delete(course)
        db.session.commit()
        
        return jsonify({'message': 'Course removed from class'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/classes/<int:class_id>/students/<int:student_id>', methods=['DELETE'])
@admin_or_session_required
def remove_student_from_class(class_id, student_id):
    """Remove a student from a class"""
    try:
        enrollment = Enrollment.query.filter_by(class_id=class_id, student_id=student_id).first_or_404()
        db.session.delete(enrollment)
        db.session.commit()
        
        return jsonify({'message': 'Student removed from class'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/classes/<int:class_id>/sessions', methods=['POST'])
@admin_or_session_required
def add_class_session(class_id):
    """Add a session (course instance) to a class schedule"""
    try:
        data = request.get_json()
        # Expects: course_name, teacher_id (optional, can infer), day_of_week, start_time, end_time, room
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        required = ['course_name', 'day_of_week', 'start_time', 'end_time']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400

        course_name = data['course_name']
        day = int(data['day_of_week'])
        start_str = data['start_time']
        end_str = data['end_time']
        room = data.get('room', 'TBD')
        
        # Parse times
        try:
            start_t = datetime.strptime(start_str, '%H:%M').time()
            end_t = datetime.strptime(end_str, '%H:%M').time()
        except ValueError:
            return jsonify({'error': 'Invalid time format. Use HH:MM'}), 400
            
        if start_t >= end_t:
            return jsonify({'error': 'Start time must be before end time'}), 400

        # Find teacher for this course (from existing assignment or provided)
        # We look for an existing course entry for this class/subject to get the teacher
        existing_course = Course.query.filter_by(class_id=class_id, name=course_name).first()
        if not existing_course:
             return jsonify({'error': 'Course subject not assigned to this class. Assign it first.'}), 400
        
        teacher_id = existing_course.teacher_id

        # CONFLICT CHECKS
        
        # 1. Class Conflict: Can't have two sessions at same time
        class_conflict = Course.query.filter(
            Course.class_id == class_id,
            Course.day_of_week == day,
            Course.start_time < end_t,
            Course.end_time > start_t
        ).first()
        
        if class_conflict:
            return jsonify({'error': f'Class Conflict: Class already has "{class_conflict.name}" at this time'}), 409

        # 2. Teacher Conflict: Teacher can't be in two places
        teacher_conflict = Course.query.filter(
            Course.teacher_id == teacher_id,
            Course.day_of_week == day,
            Course.start_time < end_t,
            Course.end_time > start_t
        ).first()
        
        if teacher_conflict:
            return jsonify({'error': f'Teacher Conflict: Teacher is busy with "{teacher_conflict.name}" (Class {teacher_conflict.class_id})'}), 409

        # 3. Room Conflict: Room can't be used twice (if room is specified and not TBD)
        if room and room.upper() != 'TBD':
            room_conflict = Course.query.filter(
                Course.room == room,
                Course.day_of_week == day,
                Course.start_time < end_t,
                Course.end_time > start_t
            ).first()
            
            if room_conflict:
                return jsonify({'error': f'Room Conflict: Room {room} is occupied by "{room_conflict.name}"'}), 409

        # Create new Session (Course entry)
        new_session = Course()
        new_session.class_id = class_id
        new_session.name = course_name
        new_session.teacher_id = teacher_id
        new_session.day_of_week = day
        new_session.start_time = start_t
        new_session.end_time = end_t
        new_session.room = room
        
        # Default dates
        today = datetime.now().date()
        new_session.start_date = today
        new_session.end_date = today + timedelta(days=120)

        db.session.add(new_session)
        db.session.commit()

        # Return the created session data
        teacher = User.query.get(new_session.teacher_id)
        teacher_name = teacher.full_name or teacher.username if teacher else "Unknown"
        
        session_data = {
            'id': new_session.id,
            'name': new_session.name,
            'teacher_id': new_session.teacher_id,
            'teacher_name': teacher_name,
            'start_time': new_session.start_time.strftime('%H:%M'),
            'end_time': new_session.end_time.strftime('%H:%M'),
            'room': new_session.room,
            'day_of_week': new_session.day_of_week
        }

        return jsonify({'message': 'Session added successfully', 'session': session_data}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
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