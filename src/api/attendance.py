# src/api/attendance.py - Attendance API endpoints

from flask import Blueprint, request, jsonify, session, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models import User, AttendanceRecord, AttendanceSession, Class, Course
from functools import wraps

attendance_bp = Blueprint('attendance', __name__)

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

@attendance_bp.route('/', methods=['GET'])
@session_or_jwt_required
def get_attendance():
    return jsonify([])

@attendance_bp.route('/start', methods=['POST'])
@session_or_jwt_required
def start_session():
    return jsonify({'message': 'Session started'}), 201

@attendance_bp.route('/recent', methods=['GET'])
@session_or_jwt_required
def get_recent_attendance():
    """Get recent attendance records for current user"""
    user = g.user

    # Get recent attendance records (last 10)
    records = AttendanceRecord.query.filter_by(student_id=user.id)\
        .join(AttendanceSession)\
        .order_by(AttendanceRecord.detected_at.desc())\
        .limit(10)\
        .all()

    result = []
    for record in records:
        # Get class and course info
        session_obj = record.session
        class_obj = Class.query.get(session_obj.class_id)

        result.append({
            'date': record.detected_at.strftime('%Y-%m-%d') if record.detected_at else 'N/A',
            'time': record.detected_at.strftime('%H:%M') if record.detected_at else 'N/A',
            'class_name': class_obj.name if class_obj else 'Unknown Class',
            'status': record.status.value,
            'confidence': float(record.confidence_score) if record.confidence_score else None
        })

    return jsonify(result)