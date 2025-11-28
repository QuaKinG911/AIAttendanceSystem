from flask import Blueprint, jsonify, g
from src.api.attendance import session_or_jwt_required
from src.models import db, User, Class, Course, AttendanceSession, AttendanceRecord, AttendanceStatus
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
        
        analytics = []
        
        for course in courses:
            class_obj = Class.query.get(course.class_id)
            if not class_obj:
                continue
                
            # Get all sessions for this class (filtered by course/teacher implicitly via class_id for now)
            # Note: In a real app, we might want to filter sessions by course_id if multiple teachers teach the same class
            sessions = AttendanceSession.query.filter_by(class_id=class_obj.id).all()
            total_sessions = len(sessions)
            
            # Calculate average attendance
            total_attendance_rate = 0
            recent_sessions_count = 0
            
            # Get total students in class (assuming we have a way to count them, 
            # for now we'll count unique students who have attended or are enrolled)
            # Since we don't have an explicit enrollment table in the models shown so far,
            # we might have to estimate or use a placeholder. 
            # Let's assume all students in the system are potential students for simplicity 
            # or better, count unique students who have attendance records for this class.
            
            # A better approach if Enrollment model exists:
            # total_students = Enrollment.query.filter_by(class_id=class_obj.id).count()
            
            # Fallback: Count unique students from attendance records for this class
            unique_students = db.session.query(AttendanceRecord.student_id)\
                .join(AttendanceSession)\
                .filter(AttendanceSession.class_id == class_obj.id)\
                .distinct().count()
            
            total_students = unique_students if unique_students > 0 else 0
            
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