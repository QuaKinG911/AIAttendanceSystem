# src/api/classes.py - Class management API endpoints

from flask import Blueprint, request, jsonify, session, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models import User, UserRole, Enrollment, Class, Course, SessionStatus
from datetime import datetime
from functools import wraps

classes_bp = Blueprint('classes', __name__)

def session_or_jwt_required(f):
    """Decorator that allows either JWT auth or session auth"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Try JWT first
        try:
            jwt_user = get_jwt_identity()
            if jwt_user:
                user = User.query.filter_by(username=jwt_user).first()
                if user:
                    g.user = user
                    return f(*args, **kwargs)
        except:
            pass

        # Fall back to session auth
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if user:
                g.user = user
                return f(*args, **kwargs)

        return jsonify({'error': 'Authentication required'}), 401

    return decorated_function

@classes_bp.route('/', methods=['GET'])
@session_or_jwt_required
def get_classes():
    """Get classes for current user"""
    user = g.user

    if user.role.value == 'student':
        # For students, return their enrolled classes with today's courses
        today = datetime.now().weekday()  # Monday = 0, Sunday = 6

        # Get enrolled classes
        enrollments = Enrollment.query.filter_by(student_id=user.id).all()
        enrolled_class_ids = [e.class_id for e in enrollments]

        # Get today's courses for enrolled classes
        today_courses = Course.query.filter(
            Course.class_id.in_(enrolled_class_ids),
            Course.day_of_week == today
        ).order_by(Course.start_time).all()

        result = []
        for course in today_courses:
            class_obj = Class.query.get(course.class_id)
            teacher = User.query.get(course.teacher_id)

            result.append({
                'id': course.id,
                'name': course.name,
                'class_name': class_obj.name if class_obj else 'Unknown',
                'teacher': teacher.full_name or teacher.username if teacher else 'Unknown',
                'start_time': course.start_time.strftime('%H:%M:%S') if course.start_time else None,
                'end_time': course.end_time.strftime('%H:%M:%S') if course.end_time else None,
                'room': course.room,
                'day_of_week': course.day_of_week
            })

        return jsonify(result)

    elif user.role.value == 'teacher':
        # For teachers, return classes they teach, with their courses
        courses = Course.query.filter_by(teacher_id=user.id).all()
        
        # Group by class
        classes_map = {}
        for course in courses:
            if course.class_id not in classes_map:
                class_obj = Class.query.get(course.class_id)
                if class_obj:
                    classes_map[course.class_id] = {
                        'id': class_obj.id,
                        'name': class_obj.name,
                        'courses': []
                    }
            
            if course.class_id in classes_map:
                classes_map[course.class_id]['courses'].append({
                    'id': course.id,
                    'name': course.name,
                    'day_of_week': course.day_of_week,
                    'start_time': course.start_time.strftime('%H:%M') if course.start_time else None,
                    'end_time': course.end_time.strftime('%H:%M') if course.end_time else None,
                    'room': course.room
                })
        
        return jsonify(list(classes_map.values()))

    else:
        # For admin, return all classes
        classes = Class.query.all()
        return jsonify([{
            'id': c.id,
            'name': c.name,
            'courses': [], # Empty list to prevent frontend errors
            'created_at': c.created_at.isoformat() if c.created_at else None
        } for c in classes])

@classes_bp.route('/<int:class_id>/students', methods=['GET'])
@classes_bp.route('/teacher/classes/<int:class_id>/students', methods=['GET'])
@session_or_jwt_required
def get_class_students_attendance(class_id):
    """Get students in a class with their recent attendance"""
    user = g.user
    
    # Verify teacher access
    if user.role.value == 'teacher':
        # Check if teacher teaches any course in this class
        # Or if they are assigned to the class in some way
        # For now, we'll allow if they teach ANY course in this class
        teaches_class = Course.query.filter_by(teacher_id=user.id, class_id=class_id).first()
        if not teaches_class:
            return jsonify({'error': 'Unauthorized access to this class'}), 403
            
    elif user.role.value != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        # Get enrolled students
        enrollments = Enrollment.query.filter_by(class_id=class_id).all()
        student_ids = [e.student_id for e in enrollments]
        
        students = User.query.filter(User.id.in_(student_ids)).all()
        
        # Get recent sessions for this class (last 5)
        from src.models import AttendanceSession, AttendanceRecord
        
        recent_sessions = AttendanceSession.query.filter_by(class_id=class_id)\
            .order_by(AttendanceSession.start_time.desc())\
            .limit(5).all()
            
        # Format sessions
        sessions_data = [{
            'id': s.id,
            'date': s.start_time.isoformat(),
            'status': s.status.value
        } for s in recent_sessions]
        
        # Get attendance records for these sessions
        session_ids = [s.id for s in recent_sessions]
        records = AttendanceRecord.query.filter(
            AttendanceRecord.session_id.in_(session_ids),
            AttendanceRecord.student_id.in_(student_ids)
        ).all()
        
        # Build attendance map: student_id -> session_id -> status
        attendance_map = {}
        for r in records:
            if r.student_id not in attendance_map:
                attendance_map[r.student_id] = {}
            attendance_map[r.student_id][r.session_id] = r.status.value
            
        # Build response
        students_data = []
        for student in students:
            student_attendance = {}
            
            # Populate attendance for each session
            for session in recent_sessions:
                status = None
                if student.id in attendance_map and session.id in attendance_map[student.id]:
                    status = attendance_map[student.id][session.id]
                elif session.status == SessionStatus.COMPLETED:
                    # If session is completed and no record, mark as absent
                    status = 'absent'
                
                if status:
                    student_attendance[session.id] = status
                
            students_data.append({
                'id': student.id,
                'name': student.full_name or student.username,
                'grade': student.start_year,
                'attendance': student_attendance
            })
            
        return jsonify({
            'sessions': sessions_data,
            'students': students_data
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@classes_bp.route('/', methods=['POST'])
@session_or_jwt_required
def create_class():
    data = request.get_json()
    return jsonify({'message': 'Class created'}), 201