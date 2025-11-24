# src/api/analytics.py - Analytics API endpoints

from flask import Blueprint, request, jsonify, session, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models import User, UserRole, AttendanceRecord
from functools import wraps

analytics_bp = Blueprint('analytics', __name__)

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

@analytics_bp.route('/trends', methods=['GET'])
@session_or_jwt_required
def get_trends():
    return jsonify({'trends': []})

@analytics_bp.route('/performance', methods=['GET'])
@session_or_jwt_required
def get_performance():
    return jsonify({'performance': []})

@analytics_bp.route('/anomalies', methods=['GET'])
@session_or_jwt_required
def get_anomalies():
    """Get system anomalies and alerts"""
    # For now, return empty list - can be implemented with actual anomaly detection
    return jsonify([])

@analytics_bp.route('/dashboard', methods=['GET'])
@session_or_jwt_required
def get_dashboard():
    """Get attendance dashboard data for current user"""
    user = g.user

    # Get attendance records for this user
    records = AttendanceRecord.query.filter_by(student_id=user.id).all()

    # Calculate attendance breakdown
    total_records = len(records)
    present_count = sum(1 for r in records if r.status.value == 'present')
    late_count = sum(1 for r in records if r.status.value == 'late')
    absent_count = sum(1 for r in records if r.status.value == 'absent')

    return jsonify({
        'attendance_breakdown': {
            'present': present_count,
            'late': late_count,
            'absent': absent_count
        },
        'total_sessions': total_records,
        'attendance_rate': round((present_count / total_records * 100) if total_records > 0 else 0, 1)
    })