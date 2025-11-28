from flask import Blueprint, jsonify, g, request
from src.api.attendance import session_or_jwt_required
from src.models import db, User, Class, Course, AttendanceSession, AttendanceRecord, AttendanceStatus, Enrollment
from src.analytics import get_attendance_trends, detect_anomalies
from sqlalchemy import func
from datetime import datetime

import logging

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')
logger = logging.getLogger(__name__)

@analytics_bp.route('/teacher/classes', methods=['GET'])
@session_or_jwt_required
def get_teacher_class_analytics():
    """Get attendance analytics for classes taught by the current teacher"""
    user = g.user
    
    if user.role.value != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
        
    try:
        # Get courses taught by this teacher
        courses = Course.query.filter_by(teacher_id=user.id).all()
        
        # Get unique class IDs from courses
        class_ids = set(course.class_id for course in courses)
        
        analytics = []
        
        for class_id in class_ids:
            class_obj = Class.query.get(class_id)
            if not class_obj:
                continue
                
            # Get all sessions for this class
            sessions = AttendanceSession.query.filter_by(class_id=class_obj.id).all()
            total_sessions = len(sessions)
            
            # Calculate average attendance
            total_attendance_rate = 0
            
            # Get total students in class using Enrollment model
            total_students = Enrollment.query.filter_by(class_id=class_obj.id).count()
            
            if total_sessions > 0:
                # Calculate attendance rate per session
                for session in sessions:
                    # Count present/late
                    present_count = AttendanceRecord.query.filter(
                        AttendanceRecord.session_id == session.id,
                        AttendanceRecord.status.in_([AttendanceStatus.PRESENT, AttendanceStatus.LATE])
                    ).count()
                    
                    # If we know total students, we can calculate rate. 
                    # If total_students is 0 (no records yet), rate is 0.
                    if total_students > 0:
                        rate = (present_count / total_students) * 100
                    else:
                        rate = 0
                    
                    total_attendance_rate += rate
                
                avg_attendance = total_attendance_rate / total_sessions
            else:
                avg_attendance = 0
                
            analytics.append({
                'class_name': class_obj.name,
                'average_attendance': round(avg_attendance, 1),
                'total_sessions': total_sessions,
                'total_students': total_students,
                'recent_sessions': len([s for s in sessions if (datetime.now().date() - s.session_date).days < 7])
            })
            
        return jsonify(analytics)
        
    except Exception as e:
        logger.error(f"Analytics Error: {e}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/dashboard', methods=['GET'])
@session_or_jwt_required
def get_student_dashboard_analytics():
    """Get attendance analytics for the student dashboard"""
    user = g.user
    
    if user.role.value != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
        
    try:
        # Get all attendance records for this student
        records = AttendanceRecord.query.filter_by(student_id=user.id).all()
        
        present_count = 0
        late_count = 0
        absent_count = 0
        
        for record in records:
            if record.status == AttendanceStatus.PRESENT:
                present_count += 1
            elif record.status == AttendanceStatus.LATE:
                late_count += 1
            elif record.status == AttendanceStatus.ABSENT:
                absent_count += 1
                
        return jsonify({
            'attendance_breakdown': {
                'present': present_count,
                'late': late_count,
                'absent': absent_count
            }
        })
        
    except Exception as e:
        logger.error(f"Dashboard Analytics Error: {e}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/trends', methods=['GET'])
@session_or_jwt_required
def get_trends():
    """Get attendance trends"""
    try:
        days = int(request.args.get('days', 30))
        trends = get_attendance_trends(days=days)
        return jsonify(trends)
    except Exception as e:
        logger.error(f"Trends Error: {e}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/anomalies', methods=['GET'])
@session_or_jwt_required
def get_anomalies():
    """Get attendance anomalies"""
    try:
        anomalies = detect_anomalies()
        
        formatted_anomalies = []
        for a in anomalies:
            if a['type'] == 'low_attendance':
                message = f"Low attendance detected ({a['rate']}%)"
            else:
                message = "Anomaly detected"
                
            formatted_anomalies.append({
                'type': a['type'],
                'class_id': a['class_id'],
                'message': message,
                'timestamp': datetime.now().isoformat()
            })
            
        return jsonify(formatted_anomalies)
    except Exception as e:
        logger.error(f"Anomalies Error: {e}")
        return jsonify({'error': str(e)}), 500