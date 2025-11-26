# src/api/classes.py - Class management API endpoints

from flask import Blueprint, request, jsonify, session, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models import User, UserRole, Enrollment, Class, Course
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

    else:
        # For other roles, return all classes (admin/teacher)
        classes = Class.query.all()
        return jsonify([{
            'id': c.id,
            'name': c.name,
            'created_at': c.created_at.isoformat() if c.created_at else None
        } for c in classes])

@classes_bp.route('/', methods=['POST'])
@session_or_jwt_required
def create_class():
    data = request.get_json()
    return jsonify({'message': 'Class created'}), 201